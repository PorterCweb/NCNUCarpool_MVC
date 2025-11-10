# MVC 架構設計說明

## 📐 為什麼選擇 MVC 架構？

### 1. 清晰的職責分離

**問題**: 原始程式碼將資料處理、業務邏輯、訊息格式化混在一起，難以維護。

**解決方案**: MVC 強制分離三大關注點
- **Model**: 「資料長什麼樣？」
- **View**: 「要怎麼呈現？」
- **Controller**: 「要做什麼？」

### 2. 可測試性

每一層都可以獨立測試：
```python
# 測試 Model - 不需要 LINE Bot
def test_activity_is_full():
    activity = DriverActivity(...)
    assert activity.is_full()

# 測試 View - 不需要資料庫
def test_format_message():
    text = line_view.format_driver_detail(mock_activity)
    assert '共乘編號' in text

# 測試 Controller - Mock Model 和 View
def test_reserve():
    result = controller.reserve_driver_as_passenger(...)
    assert result[0] == True
```

### 3. 可維護性

- 改 UI → 只改 View
- 改資料庫 → 只改 Model
- 改邏輯 → 只改 Controller
- 互不影響！

## 🏛️ 架構層次詳解

### Layer 1: Model（資料層）

#### activity_model.py - 資料模型

**設計決策**：
- 使用 `@dataclass` 減少樣板代碼
- 每個模型都有自己的業務方法
- 不依賴外部服務

```python
@dataclass
class DriverActivity(Activity):
    passengers: List[User]
    
    def is_full(self) -> bool:
        """業務規則在 Model 中"""
        limit = self.get_limit_number()
        return limit and len(self.passengers) >= limit
```

**為什麼這樣設計？**
- ✅ 業務規則與資料緊密綁定
- ✅ 可以獨立測試
- ✅ 可以在任何地方重用

#### repository.py - 資料存取層

**設計模式**: Repository Pattern

**為什麼用 Repository？**
1. **抽象資料來源**: 今天用 Google Sheets，明天可以換 PostgreSQL
2. **統一介面**: 所有資料操作都透過 Repository
3. **快取管理**: 統一管理資料快取

```python
class ActivityRepository:
    def get_all_driver_activities(self) -> List[DriverActivity]:
        """返回活動物件，不是原始資料"""
        data = self._driver_data_cache
        return [ActivityFactory.create_driver_activity(row, i) 
                for i, row in enumerate(data[1:])]
```

**優點**：
- ✅ Controller 不需要知道資料從哪來
- ✅ 可以輕鬆切換資料來源
- ✅ 集中管理 API 限制和重試邏輯

### Layer 2: View（視圖層）

#### line_view.py - LINE Bot 視圖

**設計決策**：
- 所有訊息格式化邏輯都在這裡
- 使用靜態方法，無狀態
- 不依賴 Model 的內部實作

```python
class LineMessageView:
    @staticmethod
    def format_driver_detail(activity: DriverActivity) -> str:
        """接收 Model，返回格式化字串"""
        return f'📎共乘編號：{activity.carpool_id}\n...'
```

**為什麼這樣設計？**
- ✅ 改 UI 文字不影響邏輯
- ✅ 可以輕鬆 A/B 測試不同版本
- ✅ 多語言支援容易實作

#### email_view.py - Email 視圖

**設計決策**：
- 返回 `(subject, body)` tuple
- HTML 格式與業務邏輯分離

```python
class EmailMessageView:
    @staticmethod
    def format_driver_full_email(activity: DriverActivity) -> tuple:
        subject = '活動已額滿'
        body = f'<html>...'
        return subject, body
```

**優點**：
- ✅ Email 模板可以外部化
- ✅ 支援多種格式（HTML, Plain Text）
- ✅ 容易測試

### Layer 3: Controller（控制層）

#### activity_controller.py - 活動控制器

**職責**: 查詢活動資料

```python
class ActivityController:
    def get_all_driver_activities(self):
        self.repository.refresh_driver_activities()  # Model
        return self.repository.get_all_driver_activities()  # Model
    
    def format_driver_activities_carousel(self, activities):
        return line_view.format_driver_carousel(activities)  # View
```

**設計原則**：
- ✅ 協調 Model 和 View
- ✅ 不包含格式化邏輯
- ✅ 不包含資料存取邏輯

#### reservation_controller.py - 預約控制器

**職責**: 處理預約業務邏輯

```python
class ReservationController:
    def reserve_driver_as_passenger(self, index, user):
        # 1. 取得資料 (Model)
        activity = self.repository.get_driver_activity_by_index(index)
        
        # 2. 業務驗證 (Model + Controller)
        if activity.is_user_passenger(user.user_id):
            return False, line_view.ERROR_ALREADY_RESERVED_AS_PASSENGER
        
        # 3. 執行操作 (Model)
        success = self.repository.add_passenger_to_driver_activity(index, user)
        
        # 4. 格式化回應 (View)
        message = line_view.format_reservation_success(activity, '乘客')
        
        return True, message, activity
```

**為什麼這樣分層？**
- ✅ 業務邏輯集中在一處
- ✅ 容易測試（Mock Repository 和 View）
- ✅ 可以重用於不同介面（LINE, Web, API）

#### notification_controller.py - 通知控制器

**職責**: 自動通知邏輯

**設計決策**：
- 使用 Schedule 定期檢查
- 追蹤已處理的活動（避免重複通知）
- 解耦時間判斷和通知發送

```python
class NotificationController:
    def check_driver_notifications(self):
        activities = self.repository.get_all_driver_activities()
        
        for activity in activities:
            if self.should_notify(activity.time):
                # 決定通知類型
                if not activity.is_valid_limit():
                    subject, body = email_view.format_driver_no_limit_email(activity)
                # 發送通知
                email_service.send_email(activity.email, subject, body)
```

**優點**：
- ✅ 通知邏輯與其他功能隔離
- ✅ 容易修改通知時機
- ✅ 可以輕鬆新增其他通知方式（SMS, Push）

### Layer 4: Service（服務層）

**為什麼需要 Service 層？**
- Controller 不應該直接呼叫外部 API
- 封裝第三方服務的細節
- 提供簡潔的介面

#### line_service.py - LINE API 服務

```python
class LineService:
    def reply_text(self, reply_token: str, text: str):
        """簡單的介面，隱藏 LINE API 複雜性"""
        with ApiClient(self.configuration) as api_client:
            line_bot_api = MessagingApi(api_client)
            line_bot_api.reply_message(...)
```

**優點**：
- ✅ 如果 LINE API 改版，只需改這裡
- ✅ 可以輕鬆切換到其他通訊平台
- ✅ 容易 Mock 進行測試

#### email_service.py - Email 服務

```python
class EmailService:
    def send_email(self, to_email, subject, body_html):
        """簡單的介面，隱藏 SMTP 複雜性"""
        msg = MIMEText(body_html, 'html')
        # ... SMTP 邏輯
```

## 🔄 完整請求流程

### 範例：使用者預約司機揪團

```
1. 使用者點擊 LINE Bot 按鈕
   ↓
2. LINE Server 發送 Webhook 到 Flask
   ↓
3. app.py 接收 PostbackEvent
   |
   | 解析 postback data: "reserve_driver_passenger_1"
   ↓
4. 呼叫 reservation_controller.reserve_driver_as_passenger(1, user)
   |
   | Controller 層
   ├─→ repository.get_driver_activity_by_index(1)  # 取得資料
   |   └─→ Model 層: 從快取返回 DriverActivity 物件
   |
   ├─→ activity.is_user_passenger(user_id)  # 檢查
   |   └─→ Model 層: 執行業務規則
   |
   ├─→ repository.add_passenger_to_driver_activity(1, user)  # 更新
   |   └─→ Model 層: 更新 Google Sheets
   |
   └─→ line_view.format_reservation_success(activity, '乘客')  # 格式化
       └─→ View 層: 返回格式化訊息
   ↓
5. Controller 返回 (success=True, message="已預約...", activity)
   ↓
6. app.py 呼叫 line_service.reply_text(reply_token, message)
   ↓
7. Service 層發送訊息到 LINE Server
   ↓
8. 使用者收到確認訊息
```

## 🎯 設計決策說明

### Q1: 為什麼 Repository 要快取資料？

**A**: Google Sheets API 有配額限制，頻繁呼叫會被限速。快取可以：
- 減少 API 呼叫次數
- 提升回應速度
- 避免超過配額

### Q2: 為什麼 View 要分 LINE 和 Email？

**A**: 兩者格式差異大：
- LINE: 純文字 + Emoji + 模板訊息
- Email: HTML + CSS
- 分開管理更清晰

### Q3: 為什麼要有 ActivityFactory？

**A**: Factory Pattern 的好處：
- 集中創建邏輯
- 從原始資料轉換為物件
- 容易修改創建邏輯

### Q4: Controller 可以直接呼叫 Service 嗎？

**A**: 可以！流程通常是：
```
Controller → Repository (Model) → Service
          → View → Service
```

### Q5: 為什麼不把 Service 併入 Controller？

**A**: 
- Service 是技術細節，Controller 是業務邏輯
- Service 可以被多個 Controller 共用
- 更容易替換（例如換成其他郵件服務）

## 📊 與其他架構模式比較

### MVC vs MVVM (Model-View-ViewModel)

| 特點 | MVC | MVVM |
|-----|-----|------|
| 適用場景 | Web 後端 | 前端框架 |
| View 依賴 | Controller | ViewModel |
| 資料綁定 | 手動 | 自動 |
| 本專案適用性 | ✅ 非常適合 | ❌ 過於複雜 |

### MVC vs Clean Architecture

| 特點 | MVC | Clean Architecture |
|-----|-----|-------------------|
| 層數 | 3-4 層 | 5+ 層 |
| 複雜度 | 中 | 高 |
| 學習曲線 | 平緩 | 陡峭 |
| 本專案適用性 | ✅ 剛好 | ❌ 殺雞用牛刀 |

## 🚀 擴展性展示

### 情境 1: 新增 Telegram Bot

只需：
1. 新增 `telegram_view.py`
2. 新增 `telegram_service.py`
3. Controller **不用改**！

```python
# views/telegram_view.py
class TelegramMessageView:
    @staticmethod
    def format_driver_detail(activity):
        # Telegram 格式
        return f"*{activity.carpool_id}*\n..."

# app.py
@telegram_handler.add(MessageEvent)
def handle_telegram_message(event):
    activities = activity_controller.get_all_driver_activities()  # 重用！
    message = telegram_view.format_driver_carousel(activities)
    telegram_service.send_message(event.chat_id, message)
```

### 情境 2: 改用 PostgreSQL

只需：
1. 實作新的 Repository
2. 介面保持相同
3. Controller **不用改**！

```python
class PostgresRepository(ActivityRepository):
    def get_all_driver_activities(self):
        # SQL 查詢
        rows = db.execute("SELECT * FROM driver_activities")
        return [ActivityFactory.create_driver_activity(row, i) 
                for i, row in enumerate(rows)]

# app.py
# 只需切換 Repository
from models.postgres_repository import repository  # 改這行就好！
```

### 情境 3: A/B 測試不同 UI

只需：
1. 複製 View
2. 修改格式
3. 根據使用者分流

```python
# views/line_view_v2.py
class LineMessageViewV2:
    @staticmethod
    def format_driver_detail(activity):
        # 新版 UI
        return f"🚗 {activity.carpool_id}\n..."

# app.py
if user_id in ab_test_group:
    text = line_view_v2.format_driver_detail(activity)
else:
    text = line_view.format_driver_detail(activity)
```

## ✅ MVC 架構檢查清單

設計新功能時，問自己：

- [ ] **Model**: 資料結構定義了嗎？業務規則在 Model 中嗎？
- [ ] **View**: 訊息格式定義了嗎？完全不依賴業務邏輯嗎？
- [ ] **Controller**: 業務邏輯清楚嗎？只協調不實作嗎？
- [ ] **Service**: 外部 API 封裝了嗎？介面簡潔嗎？
- [ ] **測試**: 每一層都能獨立測試嗎？

## 🎓 學習資源

- [MVC Pattern - Wikipedia](https://en.wikipedia.org/wiki/Model%E2%80%93view%E2%80%93controller)
- [Repository Pattern](https://martinfowler.com/eaaCatalog/repository.html)
- [Flask Best Practices](https://flask.palletsprojects.com/en/2.3.x/patterns/)
- [Python Design Patterns](https://refactoring.guru/design-patterns/python)

## 總結

MVC 架構為本專案提供了：
1. ✅ 清晰的程式碼組織
2. ✅ 優秀的可測試性
3. ✅ 良好的可維護性
4. ✅ 強大的可擴展性
5. ✅ 容易理解和上手

這是一個平衡實用性和複雜度的最佳選擇！
