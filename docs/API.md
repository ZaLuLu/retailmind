# RetailMind API Reference Guide

This document specifies the HTTP request/response payloads, headers, auth flows, and error codes for the RetailMind API endpoints.

---

## 1. Authentication

All requests (excluding login, register, and template downloads) require a bearer JWT token:
```http
Authorization: Bearer <access_token>
```

### 1.1 Login User
* **Endpoint**: `POST /api/v1/auth/login`
* **Request Payload**:
  ```json
  {
    "username": "user@retailmind.com",
    "password": "securepassword123"
  }
  ```
* **Response Payload (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer",
    "user": {
      "id": "1d5b4d57-ea80-41c6-8731-d7a15dc4ad9f",
      "email": "user@retailmind.com",
      "currency": "INR",
      "plan": "free"
    }
  }
  ```

### 1.2 Token Rotation
* **Endpoint**: `POST /api/v1/auth/refresh`
* **Request Header**: `Authorization: Bearer <refresh_token>`
* **Response Payload (200 OK)**:
  ```json
  {
    "access_token": "eyJhbGciOi...",
    "refresh_token": "eyJhbGciOi...",
    "token_type": "bearer"
  }
  ```

---

## 2. Retail & Analytics

### 2.1 Fetch Telemetry Summary
* **Endpoint**: `GET /api/v1/retail/summary`
* **Query Parameters**:
  * `period` (optional): `mtd` | `7d` | `30d` | `90d` | `custom` (default: `mtd`)
  * `date_from` (optional): `YYYY-MM-DD` (required if `period` is `custom`)
  * `date_to` (optional): `YYYY-MM-DD` (required if `period` is `custom`)
  * `store_id` (optional): Filter calculations to a specific location UUID.
* **Response Payload (200 OK)**:
  ```json
  {
    "total_revenue": 917560.00,
    "total_cogs": 426714.80,
    "gross_profit": 490845.20,
    "overall_margin_pct": 53.49,
    "mom_revenue_change_pct": 14.50,
    "num_sales": 144,
    "top_products": [
      {
        "product_name": "Premium Boot",
        "category": "Apparel",
        "revenue": 75000.0,
        "quantity": 150.0,
        "margin_pct": 42.0
      }
    ],
    "category_breakdown": [
      {
        "category": "Apparel",
        "revenue": 75000.0,
        "cogs": 43500.0,
        "margin_pct": 42.0
      }
    ],
    "demand_signals": [
      {
        "product_name": "Premium Boot",
        "type": "spike",
        "z_score": 2.8,
        "deviation_pct": 82.5,
        "message": "Demand surge: Z-score of 2.80 (+82.5% deviation)",
        "recent_qty": 45,
        "prior_weekly_avg": 24.6
      }
    ],
    "dead_stock_alerts": [
      {
        "product_name": "Old Jacket",
        "last_sale_days_ago": 45,
        "message": "No sales in 45 days"
      }
    ],
    "margin_erosion_alerts": [],
    "ai_insight": "Apparel margins expanded 5.2% MoM, offsetting moderate sales drops.",
    "revenue_forecast_14d": [
      {
        "date": "2026-06-08",
        "revenue": 14200.00,
        "forecast_lower": 11500.00,
        "forecast_upper": 16900.00
      }
    ],
    "customer_segments": [
      {
        "segment": "Online",
        "revenue": 520050.0,
        "cogs": 312000.0,
        "margin_pct": 40.0,
        "aov": 4333.8,
        "share": 56.68,
        "mom_growth_pct": 12.4,
        "num_orders": 120
      }
    ]
  }
  ```

### 2.2 Import Transaction Data
* **Endpoint**: `POST /api/v1/retail/upload-csv`
* **Query Parameters**:
  * `store_id` (optional): Link imported records to a store context.
* **Request Payload**: Multipart Form-Data with key `file` pointing to `.csv` or `.xlsx` file.
* **Response Payload (200 OK)**:
  ```json
  {
    "message": "Successfully imported sales records.",
    "inserted": 244,
    "errors": 0
  }
  ```

---

## 3. Conversational AI Advisor

### 3.1 Stream Advisor Responses (SSE)
* **Endpoint**: `POST /api/v1/advisor/stream`
* **Request Payload**:
  ```json
  {
    "question": "What inventory adjustment do you advise for Premium Boot?",
    "context": "{\"total_revenue\": 917560.00, ...}",
    "history": [
      {
        "role": "user",
        "content": "Hello advisor."
      },
      {
        "role": "advisor",
        "content": "Greetings. How can I assist you with your store metrics today?"
      }
    ]
  }
  ```
* **Response Format**: `text/event-stream` returning data chunks:
  ```text
  data: {"chunk": "Based "}
  
  data: {"chunk": "on "}
  
  data: {"chunk": "your "}
  ```
