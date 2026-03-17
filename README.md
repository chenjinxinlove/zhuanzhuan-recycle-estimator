zhuanzhuan-recycle-estimator

转转回收 skills，发送图片或者文字快速给出回收价格

## 中文版

### name

转转回收估价

### short_description

支持图片和文字输入的二手商品估价 Skill，快速识别商品并给出回收价格范围。

### long_description

转转回收估价是一个面向二手商品的智能估价 Skill。用户可以上传图片、输入文字，或同时提供图文信息，系统会结合商品品类、品牌、型号和关键属性，输出一个可参考的回收价格范围。

这个 Skill 更适合“先了解大致能卖多少钱”的场景，不要求立即下单；即使当前信息不完整，也会尽量给出区间估价，并提示补充哪些信息能让价格更准确。

公开资料显示，转转长期聚焦二手交易与标准化服务，覆盖手机、图书、3C 数码、服装鞋帽、母婴用品、家具家电等多类商品，并提供“官方验”和回收相关服务。这个 Skill 的定位，就是把“先估价、再决定是否出售”的体验做得更轻量、更直接。

在 OpenClaw 接入侧，图片建议以临时签名地址的方式透传给 Skill，而不是直接传图片二进制。这种方式更适合 IM 场景下的多图识别、链路追踪和风控治理。

### sample_prompts

- 这台手机大概还能卖多少钱？
- 帮我估一下这部 iPhone 13
- 我发几张图，你帮我看下这台笔记本值多少
- 这是 128G 的，屏幕有一点划痕，大概什么价位？
- 这台平板能卖多少钱？
- 我不知道具体型号，你先根据图片帮我估个范围

### tags

- 二手
- 回收
- 估价
- 数码
- 手机
- 3C
- 转转

### disclaimer

本 Skill 提供的是参考性估价结果，不等同于最终成交价。实际回收价格可能因商品真实成色、功能状态、维修记录、配件情况和实时市场行情而变化。

## 英文版

### name

Zhuanzhuan Trade-In Estimator

### short_description

An AI skill for second-hand item valuation. Upload photos or describe the item to get an estimated trade-in price range.

### long_description

Zhuanzhuan Trade-In Estimator is an AI skill designed for second-hand item valuation. Users can upload photos, enter text, or provide both, and the system will identify the item category, brand, model, and key attributes to generate a reference trade-in price range.

This skill is built for the “estimate first, decide later” scenario. It does not require users to place an order, and even when information is incomplete, it will still try to return a reasonable price range while suggesting what additional details could improve the estimate.

According to Zhuanzhuan’s public information, the platform focuses on second-hand trading and standardized services across multiple categories, including phones, books, 3C electronics, apparel, baby products, furniture, and home appliances, with services such as official inspection and recycling. This skill is intended to make the valuation experience lighter, faster, and easier for users who want to know roughly how much their used item may be worth.

For OpenClaw integration, images are best passed to the skill as short-lived signed URLs instead of raw binary payloads. This fits IM-based workflows better and makes tracing, retries, and access control easier to manage.

### sample_prompts

- How much could this phone be worth?
- Estimate the trade-in value of this iPhone 13
- I’ll upload a few photos, can you estimate this laptop?
- This is the 128GB version and the screen has light scratches. What price range would it be in?
- How much is this tablet worth?
- I don’t know the exact model. Please estimate a range based on the photos.

### tags

- second-hand
- trade-in
- valuation
- electronics
- smartphone
- 3C
- Zhuanzhuan

### disclaimer

This skill provides reference estimates only and does not represent a final transaction price. Actual trade-in value may vary depending on the item’s real condition, functionality, repair history, included accessories, and current market conditions.
