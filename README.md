# 共乘阿穿 LINE Bot - MVC 架構版

這是一個遵循標準 MVC（Model-View-Controller）架構模式的 LINE Bot 共乘系統。

## 🏗️ MVC 架構說明

### Model（模型層）
負責資料結構和資料存取

```
models/
├── __init__.py
├── activity_model.py      # 資料模型定義
└── repository.py          # 資料存取層（Repository Pattern）
```

**職責**：
- 定義資料結構（DriverActivity, PassengerActivity, User）
- 封裝資料庫操作（Google Sheets CRUD）
- 實現 Repository Pattern，提供統一的資料存取介面
- 處理資料驗證和業務規則

### View（視圖層）
負責呈現邏輯和訊息格式化

```
views/
├── __init__.py
├── line_view.py           # LINE Bot 訊息模板
└── email_view.py          # Email 訊息模板
```

**職責**：
- 格式化 LINE Bot 訊息（文字、輪播、按鈕）
- 格式化 Email 訊息（HTML 模板）
- 定義所有使用者介面相關的文字和版面
- 保持視圖邏輯與業務邏輯分離

### Controller（控制器層）
負責業務邏輯和流程控制

```
controllers/
├── __init__.py
├── activity_controller.py      # 活動查詢控制器
├── reservation_controller.py   # 預約控制器
└── notification_controller.py  # 通知控制器
```

**職責**：
- 處理使用者請求
- 協調 Model 和 View
- 實現業務邏輯（預約、取消、通知）
- 錯誤處理和資料驗證

### Services（服務層）
輔助層，封裝外部服務

```
services/
├── __init__.py
├── line_service.py        # LINE Bot API 封裝
└── email_service.py       # Email 發送封裝
```

**職責**：
- 封裝第三方 API 呼叫
- 提供簡潔的服務介面
- 處理 API 認證和錯誤

## 📁 完整專案結構

```
.
├── app.py                          # 主應用程式（Flask + 事件路由）
├── config.py                       # 配置管理
├── requirements.txt                # Python 套件依賴
├── README.md                       # 說明文件
│
├── models/                         # Model 層
│   ├── __init__.py
│   ├── activity_model.py          # 資料模型
│   └── repository.py              # 資料存取層
│
├── views/                          # View 層
│   ├── __init__.py
│   ├── line_view.py               # LINE 訊息視圖
│   └── email_view.py              # Email 訊息視圖
│
├── controllers/                    # Controller 層
│   ├── __init__.py
│   ├── activity_controller.py     # 活動控制器
│   ├── reservation_controller.py  # 預約控制器
│   └── notification_controller.py # 通知控制器
│
└── services/                       # Service 層
    ├── __init__.py
    ├── line_service.py            # LINE API 服務
    └── email_service.py           # Email 服務
```

## 🎯 MVC 架構優勢

### 1. **關注點分離（Separation of Concerns）**
- Model: 專注於資料和資料庫
- View: 專注於呈現和格式化
- Controller: 專注於業務邏輯

### 2. **可測試性（Testability）**
- 每一層都可以獨立測試
- Mock 其他層的依賴

### 3. **可維護性（Maintainability）**
- 修改 UI 不影響業務邏輯
- 修改資料庫不影響呈現
- 清晰的責任劃分

### 4. **可擴展性（Scalability）**
- 容易新增新的功能
- 可以替換不同的實作
- 支援多種視圖（LINE, Web, API）

### 5. **可重用性（Reusability）**
- Controller 可以被多個 View 使用
- Model 可以被多個 Controller 使用
- Service 可以在任何地方使用

## 🔄 資料流程

```
使用者 → LINE Bot
         ↓
    Flask Webhook (app.py)
         ↓
    Controller (處理請求)
         ↓
    Model (存取資料)
         ↓
    View (格式化回應)
         ↓
    Service (發送訊息)
         ↓
    LINE Bot → 使用者
```

### 範例流程：預約司機揪團

1. **使用者點擊「預約乘客」按鈕**
2. **app.py** 接收 Postback 事件
3. **ReservationController** 處理預約邏輯
   - 檢查活動是否存在
   - 檢查是否已預約
   - 檢查是否已滿
4. **Repository** 執行資料更新
5. **LineView** 格式化成功訊息
6. **LineService** 發送訊息給使用者

## 🚀 安裝與執行

### 環境變數設定

創建 `.env` 檔案：

```env
# LINE Bot 設定
CHANNEL_ACCESS_TOKEN=your_channel_access_token
CHANNEL_SECRET=your_channel_secret

# Google Sheet 設定
GOOGLE_CREDENTIALS={"type":"service_account",...}

# Email 設定
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_password
```

### 安裝依賴

```bash
pip install -r requirements.txt
```

### 執行應用

```bash
python app.py
```

## 📚 核心類別說明

### Model 層

#### `DriverActivity / PassengerActivity`
資料模型，封裝活動資訊和業務方法
```python
activity = DriverActivity(...)
if activity.is_full():
    print("活動已滿")
```

#### `ActivityRepository`
資料存取層，提供 CRUD 操作
```python
repository.refresh_driver_activities()
activities = repository.get_all_driver_activities()
repository.add_passenger_to_driver_activity(index, user)
```

### View 層

#### `LineMessageView`
LINE Bot 訊息模板
```python
carousel = line_view.format_driver_carousel(activities)
detail_text = line_view.format_driver_detail(activity)
```

#### `EmailMessageView`
Email 訊息模板
```python
subject, body = email_view.format_driver_full_email(activity)
```

### Controller 層

#### `ActivityController`
處理活動查詢
```python
activities = activity_controller.get_all_driver_activities()
detail = activity_controller.format_driver_activity_detail(index)
```

#### `ReservationController`
處理預約邏輯
```python
success, msg, activity = reservation_controller.reserve_driver_as_passenger(index, user)
success, msg = reservation_controller.cancel_driver_reservation(index, user_id)
```

#### `NotificationController`
處理自動通知
```python
notification_controller.start_scheduler()
notification_controller.check_all_notifications()
```

## 🔧 擴展指南

### 新增功能的步驟

1. **在 Model 層新增資料方法**
   ```python
   # models/repository.py
   def new_data_method(self):
       pass
   ```

2. **在 View 層新增訊息模板**
   ```python
   # views/line_view.py
   @staticmethod
   def format_new_message():
       return "..."
   ```

3. **在 Controller 層實作業務邏輯**
   ```python
   # controllers/new_controller.py
   class NewController:
       def handle_new_feature(self):
           pass
   ```

4. **在 app.py 新增路由**
   ```python
   @line_handler.add(MessageEvent)
   def handle_new_event(event):
       controller.handle_new_feature()
   ```

### 範例：新增「分享功能」

1. **Model**: 新增 `get_shareable_link()`
2. **View**: 新增 `format_share_message()`
3. **Controller**: 實作分享邏輯
4. **app.py**: 處理「分享」按鈕點擊

## 🎓 設計模式

本專案使用的設計模式：

1. **MVC Pattern** - 整體架構
2. **Repository Pattern** - 資料存取層
3. **Factory Pattern** - ActivityFactory 創建物件
4. **Singleton Pattern** - 全局服務實例
5. **Strategy Pattern** - 不同通知策略

## 📊 與原版對比

| 項目 | 原版 | MVC 版 |
|-----|------|--------|
| 檔案數 | 1 | 16 |
| 架構模式 | 無 | MVC |
| 關注點分離 | 差 | 優秀 |
| 可測試性 | 難 | 容易 |
| 可維護性 | 低 | 高 |
| 可擴展性 | 低 | 高 |
| 程式碼重用 | 低 | 高 |

## 🧪 測試建議

```python
# 測試 Model
def test_activity_is_full():
    activity = DriverActivity(limit='5', passengers=[...])
    assert activity.is_full() == True

# 測試 Controller
def test_reserve_driver_as_passenger():
    result = controller.reserve_driver_as_passenger(1, user)
    assert result[0] == True

# 測試 View
def test_format_driver_detail():
    text = line_view.format_driver_detail(activity)
    assert '共乘編號' in text
```

## 📝 最佳實踐

1. **保持單一職責**: 每個類別只做一件事
2. **依賴注入**: Controller 依賴 Repository 介面
3. **錯誤處理**: 統一的錯誤處理機制
4. **日誌記錄**: 詳細的操作日誌
5. **文件註解**: 每個方法都有文件字串

## 🔒 安全性

- 環境變數管理敏感資訊
- 輸入驗證在 Controller 層
- Repository 層防止 SQL 注入（雖然用的是 Google Sheets）
- LINE Signature 驗證

## 🚀 未來優化

1. **加入單元測試和整合測試**
2. **實作快取機制（Redis）**
3. **非同步處理（asyncio）**
4. **API 文件（Swagger）**
5. **監控和日誌系統（ELK Stack）**
6. **容器化（Docker）**

## 📄 授權

本專案採用 MIT 授權條款

## 🤝 貢獻

歡迎提交 Issue 和 Pull Request！
