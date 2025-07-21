import discord
import responses
import utils
import asyncio
import json
import pytz
from datetime import datetime, timedelta


def read_json(path):
    with open(path, 'r') as f:
        data = json.load(f)
    return data


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.config = read_json('config.json')

        self.news_channel_id = self.config['news_channel_id']
        self.bot_operations_channel_id = self.config['operations_channel_id']

        self.test_news_channel_id = self.config['test_news_channel_id']
        self.test_bot_operations_channel_id = self.config['test_operations_channel_id']

        self.authorizedUsers = ['pnavtradez']
        self.testing = self.config["testing"]
        self.news_update_interval = 600

        if self.testing:
            self.botOperationsChannel = self.test_bot_operations_channel_id
            self.botChannel = self.test_news_channel_id
        else:
            self.botOperationsChannel = self.bot_operations_channel_id
            self.botChannel = self.news_channel_id

    async def setup_hook(self) -> None:
        self.bg_task = self.loop.create_task(self.update_news_bg_task())

    async def on_ready(self):
        print('Online')

    async def on_message(self, message):
        if message.author == self.user:
            return

        message_author = message.author.name
        msg = message.content
        if message.channel.id == self.botOperationsChannel and message_author in self.authorizedUsers:

            if message.content.lower() == '!ping':
                await message.channel.send('Pong!')

            if message.content.lower() == "!state":
                await responses.state(message)

            if message.content.lower() == "!quote":
                await responses.send_qoute(message)

            if message.content.lower() == "!today":
                await responses.today_news(message)

            if msg.strip().lower() == "!timezone":
                await responses.handle_timezone_message(self, message)

            if msg.strip() == ('!datetime'):
                await responses.handle_datetime_command(message)

            if msg.strip().startswith("!currencies:"):
                await responses.set_allowed_currencies(message)

            if msg.strip().startswith("!impacts:"):
                await responses.set_allowed_impacts(message)

            if msg.strip() == "!news":
                df = await utils.convert_timezone_and_create_csv()
                await utils.news_today(self, df, message=message, channel_id=None)

            if msg.strip().startswith("!daily:"):
                await responses.set_daily_update_time(message)

            if message.content.lower().startswith("!alerts"):
                await responses.set_alert_currencies(message)

            if message.content.lower().startswith("!alertrole:"):
                # Set the alert role ID in config.json
                try:
                    new_role_id = int(
                        message.content.split(":", 1)[-1].strip())
                    with open('config.json', 'r') as f:
                        config = json.load(f)
                    config['alert_role_id'] = new_role_id
                    with open('config.json', 'w') as f:
                        json.dump(config, f, indent=4)
                    self.config['alert_role_id'] = new_role_id
                    await message.channel.send(f"Alert role updated to <@&{new_role_id}>")
                except Exception as e:
                    await message.channel.send(f"Failed to update alert role: {e}")

    async def update_news_bg_task(self):
        await self.wait_until_ready()
        import pandas as pd
        import os
        from datetime import datetime, timedelta
        import pytz
        import aiofiles
        import json
        import discord

        alerted_events = set()
        est = pytz.timezone('US/Eastern')
        news_channel = self.get_channel(self.botChannel)
        last_check = datetime.now(est)

        def get_role_mention():
            role_id = self.config.get('alert_role_id')
            return f"<@&{role_id}>" if role_id else ""

        async def get_alert_currencies():
            async with aiofiles.open('database.json', mode='r') as file:
                database = await file.read()
            database = json.loads(database)
            return database.get('alert_currencies', [])

        def get_today_events():
            today = datetime.now(est).strftime('%d/%m/%Y')
            news_dir = os.path.join(os.path.dirname(__file__), 'news')
            csv_files = [f for f in os.listdir(news_dir) if f.endswith('.csv')]
            if not csv_files:
                return []
            latest_csv = max(csv_files, key=lambda f: os.path.getmtime(
                os.path.join(news_dir, f)))
            df = pd.read_csv(os.path.join(news_dir, latest_csv))
            events = []
            for _, row in df.iterrows():
                if str(row['impact']).lower() in ['red', 'orange'] and str(row['date']) == today:
                    events.append(row)
            return events

        while not self.is_closed():
            try:
                now = datetime.now(est)
                today_events = get_today_events()
                alert_currencies = await get_alert_currencies()
                if not alert_currencies:
                    last_check = now
                    await asyncio.sleep(60)
                    continue
                for event in today_events:
                    if str(event['currency']).upper() not in alert_currencies:
                        continue
                    event_time_str = str(event['time'])
                    if event_time_str in ["", "All Day", "Day 1", "Day 2", "Tentative"]:
                        continue
                    try:
                        event_time = datetime.strptime(
                            f"{event['date']} {event_time_str}", "%d/%m/%Y %I:%M%p")
                    except ValueError:
                        try:
                            event_time = datetime.strptime(
                                f"{event['date']} {event_time_str}", "%d/%m/%Y %H:%M")
                        except Exception:
                            continue
                    event_time = est.localize(event_time)
                    color = 0xE74C3C if str(
                        event['impact']).lower() == 'red' else 0xF39C12
                    role_mention = get_role_mention()
                    # 5-min alert
                    if (event_time - now).total_seconds() <= 300 and (event_time - now).total_seconds() > 240:
                        alert_id = f"{event['date']}_{event['time']}_{event['currency']}_{event['event']}_5min"
                        if alert_id not in alerted_events:
                            embed = discord.Embed(
                                title=f"{event['impact'].capitalize()} Impact News Alert",
                                description=f"{event['event']}",
                                color=color
                            )
                            embed.add_field(
                                name="Currency", value=event['currency'], inline=True)
                            embed.add_field(name="Time (EST)",
                                            value=event['time'], inline=True)
                            embed.add_field(
                                name="Alert", value="5 minutes before", inline=False)
                            await news_channel.send(content=role_mention, embed=embed)
                            alerted_events.add(alert_id)
                    # At-release alert (only trigger if event_time just passed within the last minute)
                    delta = (now - event_time).total_seconds()
                    if 0 <= delta < 60:
                        alert_id = f"{event['date']}_{event['time']}_{event['currency']}_{event['event']}_release"
                        if alert_id not in alerted_events:
                            embed = discord.Embed(
                                title=f"{event['impact'].capitalize()} Impact News Alert",
                                description=f"{event['event']}",
                                color=color
                            )
                            embed.add_field(
                                name="Currency", value=event['currency'], inline=True)
                            embed.add_field(name="Time (EST)",
                                            value=event['time'], inline=True)
                            embed.add_field(
                                name="Alert", value="NOW!", inline=False)
                            await news_channel.send(content=role_mention, embed=embed)
                            alerted_events.add(alert_id)
                last_check = now
            except FileNotFoundError:
                print("News CSV file not found. Skipping this update.")
            except asyncio.CancelledError:
                print("Background task cancelled.")
                break
            await asyncio.sleep(60)  # Check every minute


if __name__ == "__main__":
    try:
        client = MyClient(intents=discord.Intents.all())
        client.run(client.config['token'])
    except KeyboardInterrupt:
        pass  # Ignore, will print in finally
    finally:
        print("Bot Offline...")
