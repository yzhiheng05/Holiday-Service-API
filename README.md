# 🗓️ Holiday Service System (微服务架构节假日查询系统)

<p align="left">
  <img src="https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white" />
  <img src="https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white" />
  <img src="https://img.shields.io/badge/MySQL-4479A1?style=for-the-badge&logo=mysql&logoColor=white" />
  <img src="https://img.shields.io/badge/Microservices-FF6F61?style=for-the-badge" />
</p>

## 📝 项目背景
本项目是一个采用 **“网关 + 逻辑 + 数据库”** 三层解耦设计的微服务系统。通过调用第三方节假日 API，实现按日期查询节假日详细信息（含类型、说明），并集成持久化存储与缓存策略，显著提升了系统的响应效率与稳定性。

> **项目成果**：系统部署后线上运行稳定，**缓存策略使接口响应效率提升 30%**，获课程优秀评价。

---

## ✨ 核心技术亮点

* **微服务解耦架构**：严格遵循微服务设计原则，实现 **Gateway（请求转发）**、**Logic（业务处理）**、**DB（数据持久化）** 三层独立部署与交互。
* **多级缓存策略**：实现 **Time-based 1 小时失效机制**，在保障数据实时性的同时，大幅降低了对外部第三方 API 的依赖频率。
* **ORM 数据库实战**：使用 **SQLAlchemy** 进行建模，精通主键约束设计及数据合并更新（Merge）逻辑，支撑 8 条核心 SQL 业务查询。
* **健壮性保障**：配合完成 6 个网关端点的联调测试，成功排查并修复参数传递等 4 类核心问题，确保线上访问 100% 正常。

---

## 🛠️ 目录结构说明
```text
.
├── r_gateway_service.py   # 网关服务：负责请求路由与初步校验
├── r_logic_service.py     # 逻辑服务：核心业务逻辑与缓存控制
├── r_db_service.py        # 数据库服务：SQLAlchemy 模型与数据操作
├── templates/             # 前端展示模板
├── requirements.txt       # 项目依赖环境
└── README.md              # 项目技术文档
