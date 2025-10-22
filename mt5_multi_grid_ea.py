# นายศรายุทร์ จันทร์แดง 6604101380

import threading
import time
import random
import requests
from datetime import datetime

# ---------------- MT5Bot Simulation Class ----------------
class MT5BotSim:
    QUESTDB_EXEC_URL = "http://localhost:9000/exec"  # QuestDB SQL endpoint

    def __init__(self, symbol="EURUSD", n_positions=3):
        self.symbol = symbol
        self.n_positions = n_positions

    # ---------- Simulate Position ----------
    def simulate_position(self, pos_type="buy"):
        """
        สร้าง position ปลอม สำหรับส่ง QuestDB
        """
        class FakePosition:
            def __init__(self, symbol, ticket, pos_type, volume, price_open, price_current, profit):
                self.symbol = symbol
                self.ticket = int(ticket)
                self.type = pos_type
                self.volume = float(volume)
                self.price_open = float(price_open)
                self.price_current = float(price_current)
                self.profit = float(profit)

        ticket = int(time.time() * 1000) % 100000 + random.randint(1, 999)
        volume = round(random.uniform(0.01, 0.05), 2)
        
        if "USD" in self.symbol and "XAU" not in self.symbol:
            price_open = round(random.uniform(1.10, 1.20), 5)
            price_current = round(price_open + random.uniform(-0.005, 0.005), 5)
            profit = round((price_current - price_open) * volume * 100000, 2)
        else:  # XAU
            price_open = round(random.uniform(1900, 2000), 1)
            price_current = round(price_open + random.uniform(-5, 5), 1)
            profit = round((price_current - price_open) * volume * 100, 2)

        # สำหรับ sell position ให้ profit เป็นค่าตรงข้าม
        if pos_type == "sell":
            profit = -profit

        return FakePosition(self.symbol, ticket, pos_type, volume, price_open, price_current, profit)

    # ---------- QuestDB Logging ----------
    def save_position_to_questdb(self, position):
        """
        บันทึก position ลง QuestDB ด้วย SQL INSERT
        """
        # สร้าง timestamp ในรูปแบบ microseconds
        timestamp_us = int(time.time() * 1000000)
        
        # สร้าง SQL INSERT query
        # !!! สำคัญ: ตรวจสอบว่า Table 'positions' ของคุณมี 8 คอลัมน์ตามนี้ !!!
        query = f"""
        INSERT INTO positions
        VALUES(
            '{position.symbol}',
            {position.ticket},
            '{position.type}',
            {position.volume},
            {position.price_open},
            {position.price_current},
            {position.profit},
            {timestamp_us}
        )
        """
        
        try:
            # ใช้ params={'query': ...} เพื่อให้ requests จัดการ encoding URL ให้ถูกต้อง
            r = requests.get(self.QUESTDB_EXEC_URL, params={'query': query})
            
            if r.status_code == 200:
                result = r.json()
                if 'error' in result:
                    print(f"[{self.symbol}] SQL Error: {result['error']}")
                else:
                    print(f"[{self.symbol}] ✓ Position {position.ticket} saved | Profit: {position.profit:.2f}")
            else:
                print(f"[{self.symbol}] HTTP Error: status={r.status_code}, {r.text}")
        except requests.exceptions.ConnectionError as e:
            print(f"[{self.symbol}] Exception: Cannot connect to QuestDB at {self.QUESTDB_EXEC_URL}. Is it running?")
            print(f"[{self.symbol}] Error details: {e}")
            time.sleep(5) # หยุดรอ 5 วินาที ก่อนลองใหม่
        except Exception as e:
            print(f"[{self.symbol}] Unknown Exception: {e}")

    # ---------- Run Simulation Loop ----------
    def run(self):
        print(f"[{self.symbol}] Bot started...")
        while True:
            for _ in range(self.n_positions):
                # สร้าง buy position
                pos_buy = self.simulate_position("buy")
                self.save_position_to_questdb(pos_buy)
                
                time.sleep(0.5)  # หน่วงเล็กน้อยระหว่างแต่ละ position

                # สร้าง sell position
                pos_sell = self.simulate_position("sell")
                self.save_position_to_questdb(pos_sell)
                
                time.sleep(0.5)

            time.sleep(2)  # รอก่อนรอบถัดไป

# ---------------- Main: MultiThread Simulation ----------------
if __name__ == "__main__":
    symbols = ["EURUSD", "XAUUSD", "GBPUSD"]
    bots = []

    print("=" * 60)
    print(" MT5 Position Logger Simulation")
    print("=" * 60)
    print(f"Target QuestDB: http://127.0.0.1:9000")
    print(f"Symbols: {', '.join(symbols)}")
    print(f"Positions per round: 3 buys + 3 sells per symbol")
    print("=" * 60)

    # --- (จำเป็นต้องสร้างตารางก่อนรัน) ---
    print("!!! [ACTION REQUIRED] !!!")
    print("Make sure you have created the 'positions' table in QuestDB first!")
    print("Go to http://127.0.0.1:9000 and run this SQL query:")
    print("-" * 60)
    print("CREATE TABLE IF NOT EXISTS positions (")
    print("  symbol SYMBOL INDEX,")
    print("  ticket LONG,")
    print("  type SYMBOL,")
    print("  volume DOUBLE,")
    print("  price_open DOUBLE,")
    print("  price_current DOUBLE,")
    print("  profit DOUBLE,")
    print("  timestamp TIMESTAMP")
    print(") TIMESTAMP(timestamp) PARTITION BY DAY;")
    print("-" * 60)
    
    print("\nWaiting 10 seconds to give you time to read this...")
    time.sleep(10) # หน่วงเวลาให้อ่าน

    for sym in symbols:
        bot = MT5BotSim(symbol=sym, n_positions=3)
        t = threading.Thread(target=bot.run, daemon=True)
        t.start()
        bots.append(t)
        time.sleep(0.2)  # หน่วงเล็กน้อยก่อนเริ่ม bot ถัดไป

    print("\n✓ All bots running... Press Ctrl+C to stop.\n")

    # Keep main thread alive
    try:
        while True:
            time.sleep(10)
    except KeyboardInterrupt:
        print("\n\nSimulation stopped.")
        print("Check your data at: http://127.0.0.1:9000")

