# App policy and coverage matrix

Generated from the canonical `rulekit_v4/apps.json` inventory. All **164 real records** are listed below: **132 CN + 32 international**, retaining stable IDs and app display names. There are **114 declared sources** and **28 shared dependencies**.

**No row is marked complete or phone-validated.** Candidate sources are evidence for rules, not an assertion of full app traffic coverage. **13 unresolved** and **5 local-only** records remain explicit. A local-only label describes known local functionality; it is not proof that the app can never connect.

Policy keys: `ai` = US residential fallback; `tiktok` = separate US residential fallback; `stream` = streaming Smart; `global` = ordinary international Smart; `uk` = UK fallback; `DIRECT` = domestic direct. The `google` category uses `global`, and ordinary Meta services also use `global`. Browser and mail traffic may route by destination/provider.

Coverage states distinguish independent/shared candidates, official-document evidence, existing configuration evidence and unresolved gaps. Shared dependency IDs refer to the same canonical inventory. App names preserve the supplied identities; name-only or unresolved identity does not become verified merely by listing it.

<!-- APP_MATRIX_START -->

| ID | App | Category | Coverage | Direct sources | Dependencies | Combined sources |
| --- | --- | --- | --- | ---: | ---: | ---: |
| CN001 | 支付宝 | cn | independent-candidate | 1 | 0 | 1 |
| CN002 | 云闪付 | cn | independent-candidate | 1 | 0 | 1 |
| CN003 | 中国工商银行 | cn | independent-candidate | 1 | 0 | 1 |
| CN004 | 中国建设银行 | cn | independent-candidate | 1 | 0 | 1 |
| CN005 | 个人手机银行（四川农信） | cn | official-document-only | 1 | 0 | 1 |
| CN006 | 招商银行 | cn | independent-candidate | 1 | 0 | 1 |
| CN007 | 兴业银行 | cn | official-service-candidate | 1 | 0 | 1 |
| CN008 | 动卡空间 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN009 | 掌上生活 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN010 | 京东金融 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN011 | 微信 | cn | independent-candidate | 1 | 0 | 1 |
| CN012 | 钉钉 | cn | independent-candidate | 1 | 0 | 1 |
| CN013 | QQ | cn | shared-group-candidate | 0 | 1 | 1 |
| CN014 | 抖音 | cn | independent-candidate | 1 | 0 | 1 |
| CN015 | 快手 | cn | independent-candidate | 1 | 0 | 1 |
| CN016 | 小红书 | cn | independent-candidate | 1 | 0 | 1 |
| CN017 | 哔哩哔哩 | cn | independent-candidate | 1 | 0 | 1 |
| CN018 | 微博 | cn | independent-candidate | 1 | 0 | 1 |
| CN019 | 快手极速版 | cn | independent-candidate | 1 | 0 | 1 |
| CN020 | 网易云音乐 | cn | independent-candidate | 1 | 0 | 1 |
| CN021 | 腾讯视频 | cn | independent-candidate | 1 | 0 | 1 |
| CN022 | 爱奇艺 | cn | independent-candidate | 1 | 0 | 1 |
| CN023 | 音乐 | cn | independent-candidate | 1 | 3 | 4 |
| CN024 | 剪映 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN025 | 王者荣耀 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN026 | 掌上英雄联盟 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN027 | 飞智游戏厅 | cn | existing-config-candidate | 1 | 0 | 1 |
| CN028 | 酷安 | cn | independent-candidate | 1 | 0 | 1 |
| CN029 | 猫眼 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN030 | 淘票票 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN031 | 播客 | cn | independent-candidate | 1 | 3 | 4 |
| CN032 | 视频（Apple TV） | cn | independent-candidate | 1 | 3 | 4 |
| CN033 | 淘宝 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN034 | 京东 | cn | independent-candidate | 1 | 0 | 1 |
| CN035 | 拼多多 | cn | independent-candidate | 1 | 0 | 1 |
| CN036 | 闲鱼 | cn | independent-candidate | 2 | 0 | 2 |
| CN037 | 美团 | cn | independent-candidate | 1 | 0 | 1 |
| CN038 | 淘宝闪购 | cn | independent-candidate | 1 | 0 | 1 |
| CN039 | 大众点评 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN040 | 盒马 | cn | independent-candidate | 1 | 0 | 1 |
| CN041 | 山姆会员商店 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN042 | 得物 | cn | independent-candidate | 1 | 0 | 1 |
| CN043 | 转转 | cn | independent-candidate | 1 | 0 | 1 |
| CN044 | 阿里巴巴（1688） | cn | shared-group-candidate | 0 | 1 | 1 |
| CN045 | 京东AI购 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN046 | 一淘 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN047 | 京粉 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN048 | 省钱快报 | cn | existing-config-candidate | 1 | 0 | 1 |
| CN049 | 高德地图 | cn | independent-candidate | 1 | 0 | 1 |
| CN050 | 地图 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN051 | DeepSeek | cn | independent-candidate | 1 | 0 | 1 |
| CN052 | 豆包 | cn | independent-candidate | 1 | 0 | 1 |
| CN053 | 千问 | cn | shared-group-candidate | 1 | 1 | 2 |
| CN054 | ima | cn | shared-group-candidate | 0 | 1 | 1 |
| CN055 | TRAE | cn | independent-candidate | 1 | 0 | 1 |
| CN056 | Marvis | cn | shared-group-candidate | 0 | 1 | 1 |
| CN057 | 铁路12306 | cn | independent-candidate | 1 | 0 | 1 |
| CN058 | 携程旅行 | cn | independent-candidate | 1 | 0 | 1 |
| CN059 | 航旅纵横 | cn | existing-config-candidate | 1 | 0 | 1 |
| CN060 | 哈啰 | cn | existing-config-candidate | 1 | 0 | 1 |
| CN061 | 天府通 | cn | official-service-candidate | 1 | 0 | 1 |
| CN062 | 无忧行 | cn | official-service-candidate | 1 | 0 | 1 |
| CN063 | 懂车帝 | cn | independent-candidate | 1 | 0 | 1 |
| CN064 | 汽车之家 | cn | official-service-candidate | 1 | 0 | 1 |
| CN065 | 吉利汽车 | cn | independent-candidate | 1 | 0 | 1 |
| CN066 | 九号出行 | cn | existing-config-candidate | 1 | 0 | 1 |
| CN067 | 电话 | cn | shared-service-candidate | 0 | 2 | 2 |
| CN068 | 信息 | cn | shared-service-candidate | 0 | 4 | 4 |
| CN069 | Safari浏览器 | cn | target-site-routing | 0 | 5 | 5 |
| CN070 | 照片 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN071 | 相机 | cn | local-only | 0 | 0 | 0 |
| CN072 | 日历 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN073 | 邮件 | cn | mail-provider-routing | 0 | 3 | 3 |
| CN074 | 备忘录 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN075 | 提醒事项 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN076 | 天气 | cn | shared-service-candidate | 0 | 2 | 2 |
| CN077 | 健康 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN078 | 钱包 | cn | shared-service-candidate | 0 | 2 | 2 |
| CN079 | 计算器 | cn | local-only | 0 | 0 | 0 |
| CN080 | 文件 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN081 | 设置 | cn | shared-service-candidate | 0 | 4 | 4 |
| CN082 | App Store | cn | shared-service-candidate | 0 | 3 | 3 |
| CN083 | Watch | cn | shared-service-candidate | 0 | 5 | 5 |
| CN084 | 查找 | cn | shared-service-candidate | 1 | 4 | 5 |
| CN085 | 健身 | cn | shared-service-candidate | 1 | 3 | 4 |
| CN086 | Grow | cn | official-document-only | 1 | 0 | 1 |
| CN087 | 米家 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN088 | 华为智慧生活 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN089 | 家庭 | cn | shared-service-candidate | 0 | 4 | 4 |
| CN090 | Numbers表格 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN091 | 网易有道词典 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN092 | 翻译 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN093 | BOSS直聘 | cn | existing-config-candidate | 1 | 0 | 1 |
| CN094 | 智联招聘 | cn | existing-config-candidate | 1 | 0 | 1 |
| CN095 | 猎聘 | cn | independent-candidate | 1 | 0 | 1 |
| CN096 | 企查查 | cn | independent-candidate | 1 | 0 | 1 |
| CN097 | 贝壳找房 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN098 | 国家网络身份认证 | cn | official-document-only | 1 | 0 | 1 |
| CN099 | 悦通行 | cn | official-document-only | 1 | 0 | 1 |
| CN100 | 去上网（去哒） | cn | unresolved | 0 | 0 | 0 |
| CN101 | 中国移动 | cn | independent-candidate | 1 | 0 | 1 |
| CN102 | UU远程 | cn | official-service-candidate | 1 | 0 | 1 |
| CN103 | 交管12123 | cn | official-service-candidate | 1 | 0 | 1 |
| CN104 | 个人所得税 | cn | official-service-candidate | 1 | 0 | 1 |
| CN105 | MONO记账 | cn | official-document-only | 1 | 0 | 1 |
| CN106 | Cookie | cn | official-document-only | 1 | 0 | 1 |
| CN107 | 上岛记 | cn | unresolved | 0 | 0 | 0 |
| CN108 | iCost | cn | unresolved | 0 | 0 | 0 |
| CN109 | 扫描全能王 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN110 | 黑猫投诉 | cn | shared-group-candidate | 0 | 1 | 1 |
| CN111 | 爱思全能版 | cn | unresolved | 0 | 0 | 0 |
| CN112 | 语音备忘录 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN113 | 指南针 | cn | local-only | 0 | 0 | 0 |
| CN114 | 测距仪 | cn | local-only | 0 | 0 | 0 |
| CN115 | 放大器 | cn | local-only | 0 | 0 | 0 |
| CN116 | 密码 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN117 | 图书 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN118 | 快捷指令 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN119 | 股市 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN120 | FaceTime通话 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN121 | 支持 | cn | shared-service-candidate | 0 | 2 | 2 |
| CN122 | 反馈 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN123 | Apple Store | cn | shared-service-candidate | 0 | 3 | 3 |
| CN124 | GestaltEdit | cn | unresolved | 0 | 0 | 0 |
| CN125 | 提示 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN126 | 无边记 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN127 | 手记 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN128 | iTunes Store | cn | shared-service-candidate | 1 | 3 | 4 |
| CN129 | 预览 | cn | shared-service-candidate | 0 | 3 | 3 |
| CN130 | 全球网测 | cn | unresolved | 0 | 0 | 0 |
| CN131 | Speedtest | cn | independent-candidate | 1 | 0 | 1 |
| CN132 | 彩云天气PRO | cn | independent-candidate | 1 | 0 | 1 |
| INT001 | ChatGPT | ai | independent-candidate | 4 | 2 | 6 |
| INT002 | Claude | ai | independent-candidate | 2 | 1 | 3 |
| INT003 | Gemini | ai | independent-candidate | 2 | 1 | 3 |
| INT004 | Cursor | ai | independent-candidate | 1 | 1 | 2 |
| INT005 | Grok | ai | independent-candidate | 1 | 1 | 2 |
| INT006 | Grok Bot | ai | shared-group-candidate | 0 | 2 | 2 |
| INT007 | X | global | independent-candidate | 1 | 0 | 1 |
| INT008 | YouTube | stream | independent-candidate | 1 | 0 | 1 |
| INT009 | TikTok | tiktok | independent-candidate | 1 | 0 | 1 |
| INT010 | Instagram | global | independent-candidate | 1 | 0 | 1 |
| INT011 | Facebook | global | independent-candidate | 1 | 0 | 1 |
| INT012 | Netflix | stream | independent-candidate | 1 | 0 | 1 |
| INT013 | Viki | stream | independent-candidate | 1 | 0 | 1 |
| INT014 | WhatsApp | global | independent-candidate | 1 | 0 | 1 |
| INT015 | Telegram | global | independent-candidate | 1 | 0 | 1 |
| INT016 | Discord | global | independent-candidate | 1 | 0 | 1 |
| INT017 | Google | google | shared-group-candidate | 0 | 1 | 1 |
| INT018 | Chrome | google | target-site-routing | 0 | 1 | 1 |
| INT019 | Gmail | google | shared-group-candidate | 0 | 1 | 1 |
| INT020 | 云端硬盘（Google Drive） | google | independent-candidate | 1 | 0 | 1 |
| INT021 | Google Maps | google | shared-group-candidate | 0 | 1 | 1 |
| INT022 | Obsidian | global | official-service-candidate | 1 | 0 | 1 |
| INT023 | DejaVocab | global | official-document-only | 1 | 0 | 1 |
| INT024 | Tableau | cn | existing-config-candidate | 1 | 0 | 1 |
| INT025 | Sanas | global | official-document-only | 1 | 0 | 1 |
| INT026 | gifgaff | uk | independent-candidate | 1 | 0 | 1 |
| INT027 | Shadowrocket | global | unresolved | 0 | 0 | 0 |
| INT028 | Surge | global | official-service-candidate | 1 | 0 | 1 |
| INT029 | PayPal | paypal | independent-candidate | 1 | 0 | 1 |
| INT030 | Wise | wise | independent-candidate | 1 | 0 | 1 |
| INT031 | Binance | binance | independent-candidate | 1 | 0 | 1 |
| INT032 | OKX | okx | independent-candidate | 1 | 0 | 1 |

<!-- APP_MATRIX_END -->

## Coverage state totals

- `existing-config-candidate`: 8
- `independent-candidate`: 58
- `local-only`: 5
- `mail-provider-routing`: 1
- `official-document-only`: 8
- `official-service-candidate`: 3
- `shared-group-candidate`: 29
- `shared-service-candidate`: 33
- `target-site-routing`: 2
- `unresolved`: 13

See [apps.json](../rulekit_v4/apps.json) for identity fields, source evidence URLs, candidate/known hosts and notes; [report.json](../dist/v4/report.json) for the latest compiled probes and exclusions. Static probe success is distinct from phone acceptance. [Setup](GETTING_STARTED.md) · [Maintenance](MAINTENANCE.md).
