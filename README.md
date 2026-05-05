# ENT208 

# 项目名称 | Project Name
Starlight AI Learning Companion（盲童AI启蒙学习助手 | 星辰语音版）

让每一个看不见的孩子，都能“听见”整个世界。
Let every child who cannot see “hear” the whole world.

# 一，项目简介 | Project Introduction

Starlight AI Learning Companion 是一个专为盲童和重度视障儿童设计的语音优先学习平台。它将视频学习、智能问答、物体识别与学习报告整合到一条温柔、清晰、可重复的学习路径中，帮助孩子通过聆听建立理解、通过表达建立自信、通过探索建立勇气。

本项目为前端完整实现，已与 FastAPI 后端完成全功能联调，支持视频上传与摘要、引导式学习、星辰语音助手（含唤醒词与日常聊天）、智能识物系统（YOLO + Coze 双模式）、学习报告与家长支持等核心功能。

项目名称中的“Starlight”与“Xingchen（星辰）”共同传递一个信念：成为黑暗世界里最亮的那颗星星。

English

Starlight AI Learning Companion is a voice-first learning platform designed specifically for blind and severely visually impaired children. It integrates video learning, intelligent Q&A, object recognition, and learning reports into a gentle, clear, and repeatable learning path. The platform helps children build understanding through listening, build confidence through speaking, and build courage through exploration.

This project is a complete frontend implementation that has been fully integrated with a FastAPI backend. It supports video upload and summarization, guided learning, the Xingchen Voice Assistant (with wake word and daily chat capabilities), a smart object recognition system (YOLO + Coze dual mode), learning reports, and parent support features.

The name “Starlight” together with “Xingchen” conveys a single belief: Become the brightest star in a dark world.

# 👥 二，目标用户 | Target Users

项目旨在为视障教育生态中的多方角色提供支持，以下是各角色的核心使用场景与需求分析：
The project is designed to support various stakeholders in the visually impaired education ecosystem. Below is the analysis of core use cases and needs for each role:

| 用户角色 (User Role) | 使用场景 (Use Case) | 核心需求 (Core Need) |
| :--- | :--- | :--- |
| **盲童 / 视障儿童**<br>*(Blind / Visually Impaired Children)* | 在家长或老师辅助下，或独立使用平板/电脑进行学习。<br>*(Learning independently or with parent/teacher assistance)* | 通过语音获取信息、回答问题、识别物体、获得陪伴感。<br>*(Access info, answer questions, recognize objects via voice)* |
| **家长**<br>*(Parents)* | 在家中辅助孩子学习，监控学习状态。<br>*(Assisting children at home and monitoring status)* | 上传教学视频、查看学习报告、了解进度、获取辅助建议。<br>*(Upload videos, view reports, obtain suggestions)* |
| **特殊教育老师**<br>*(Special Education Teachers)* | 在课堂或一对一教学场景中使用。<br>*(Using in classrooms or one-on-one sessions)* | 快速准备教学内容、评估学习效果、获得专业教学建议。<br>*(Prepare content, evaluate outcomes, receive advice)* |
| **产品演示 / 评审人员**<br>*(Demo / Review Audiences)* | 评估产品的创新性、功能完整性与设计逻辑。<br>*(Evaluating innovation, functionality, and design)* | 快速体验完整学习流程、理解设计理念与技术实现方案。<br>*(Quickly experience workflow and understand tech stack)* |

# 三，核心功能列表 | Core Features
## 3.1 视频学习模块 | Video Learning Module

- 视频上传 (Video Upload) 支持上传教学视频（mp4/mov/avi 等常见格式）(Supports common video formats)
- 绑定文本稿 (Bind Transcript)  可选上传视频对应的文字稿，提升摘要质量 (Optional transcript upload to improve summary quality)
- 生成摘要 (Generate Summary)	后端自动生成儿童友好总结 + 无障碍语音描述 + 关键词 (Backend generates child-friendly summary + accessible description + keywords)
- 引导式学习 (Guided Session)	正式学习流程：听摘要 → 回答问题 → 获得反馈 → 下一题 (Formal flow: listen → answer → get feedback → next question)
- 语音提交答案 (Voice Answer)	孩子直接说话回答，无需打字 (Children speak answers directly, no typing needed)
- 重复播放 (Replay)	支持重复播放摘要、当前问题、最近反馈 (Supports replaying summary, current question, and recent feedback)
- 答题反馈 (Answer Feedback)	正确时鼓励并进入下一题；错误时给予提示并重复本题 (Encouragement + next question on correct; hint + repeat question on incorrect)

## 3.2 星辰语音助手 | Xingchen Voice Assistant

- 按钮录音 (Button Recording)	点击按钮开始录音，再次点击停止并发送给后端 (Click to start recording, click again to stop and send to backend)
- 唤醒词持续监听 (Wake Word Listening)	无需按钮，说出“Xingchen”即可激活助手 (Say “Xingchen” to activate the assistant without pressing any button)
- 指令执行 (Command Execution)	支持语音控制：开始学习、重复问题、打开智能识物系统、切换模式等 (Voice control for: start learning, repeat question, open object detection, switch modes, etc.)
- 日常聊天 (Daily Chat)	支持开放式对话，如“讲一个星星的故事”、“今天天气怎么样” (Supports open-ended conversations like “tell me a story about stars” or “what’s the weather like”)
- ASR 纠错容错 (ASR Error Correction)	前端自动纠正常见语音识别错误（如“智能食物系统”→“智能识物系统”）(Frontend auto-corrects common ASR mistakes)
- 精灵动画反馈 (Sprite Animation Feedback)	右下角星辰精灵会根据状态变换表情（聆听、思考、开心、困惑）(The sprite changes expressions based on status: listening, thinking, happy, confused)

## 3.3 智能识物系统 | Smart Object System

- YOLO 实时检测 (YOLO Real-time Detection)	调用摄像头，实时识别画面中心物体，弹窗播报 (Uses camera to detect central object in real-time, popup + voice announcement)
- Coze 平台集成 (Coze Platform Integration)	嵌入组员开发的 Coze 识物页面，提供备选方案 (Embeds a teammate’s Coze object recognition page as a fallback option)
- 识物上报 (Object Detection Report)	将识别结果上报后端，用于数据统计 (Reports detection results to backend for data tracking)
- 学习卡片生成 (Learning Card Generation)	根据识别到的物体，生成可反复学习的内容卡片 (Generates repeatable learning cards based on detected objects)

## 3.4 家长与报告模块 | Parent & Report Module

- 儿童画像 (Child Profile)	创建/更新儿童信息（姓名、年龄组、难度偏好）(Create/update child info: name, age group, difficulty preference)
- 学习进度查询 (View Progress)	查看儿童的学习进度数据 (View child’s learning progress)
- 推荐下一步 (Recommend Next Step)	根据儿童画像推荐适合的学习内容 (Recommends suitable learning content based on profile)
- 学习报告生成 (Generate Report)	生成包含报告文本、建议行动、练习重点的完整报告 (Generates comprehensive report with text, suggested actions, practice focus)
- 家长帮助 (Parent Help)	当孩子卡住时，家长可请求系统提供提示或简化问题 (Parents can request hints or simplified questions when child is stuck)
- 意图路由 (Intent Router)	识别用户输入的文本意图（控制指令 / 问答 / 闲聊）(Recognizes user intent from text: control command / Q&A / chat)
- 会话重置 (Session Reset)	结束当前学习会话，清空状态 (Ends current learning session and clears state)

## 3.5 视觉与体验 | Visual & Experience

- 宇宙深色主题 (Deep Space Theme)	星空、银河带、星云、流星动态背景 (Starfield, Milky Way, nebula, shooting stars dynamic background)
- 玻璃拟态卡片 (Glassmorphism Cards)	毛玻璃效果，提升视觉层次 (Frosted glass effect for visual depth)
- 星辰精灵 (Xingchen Sprite)	可拖拽、会眨眼、有情绪变化的陪伴角色 (Draggable, blinking, mood-changing companion character)
- 滚动横幅 (Marquee Banner)	循环展示品牌口号 (Cycles through brand slogans)
- 响应式设计 (Responsive Design)	适配桌面、平板、手机 (Adapts to desktop, tablet, and mobile)
- 高对比度 (High Contrast)	深色背景 + 亮色文字，低视力友好 (Dark background + bright text for low-vision friendliness)

# 四、技术栈 | Tech Stack

本项目在前端采用 HTML5、CSS3 及原生 JavaScript (ES6+) 构建，确保了轻量级且高效的用户体验。核心交互由 Web Speech API 驱动，实现了唤醒词持续监听与语音答案提交；语音合成则通过 后端 edge-tts 与浏览器原生双模式 结合，提供了自然流畅的听觉反馈。视觉层面，我们利用 纯 CSS 生成 了包含银河、星云及流星的动态宇宙背景，并配合 CSS 关键帧与 JS 状态管理 赋予了“星辰精灵”生动的情感动画。此外，通过 Fetch API 实现前后端高效对接，并灵活嵌入 Coze iframe 作为第三方识物能力的补充。

The frontend is built using HTML5, CSS3, and Vanilla JavaScript (ES6+) to ensure a lightweight and high-performance user experience. Core interactions are powered by the Web Speech API, enabling continuous wake-word listening and voice answer submission. For speech synthesis, a dual-mode approach combining backend edge-tts and browser-native SpeechSynthesis provides natural and fluid auditory feedback. Visually, we utilized pure CSS to generate a dynamic deep-space background featuring the Milky Way, nebulae, and shooting stars, while CSS keyframes and JS state management bring the "Xingchen Sprite" to life with emotive animations. Additionally, the Fetch API facilitates seamless backend integration, complemented by an embedded Coze iframe as a robust third-party solution for object recognition.

# 五、工作流 | Workflows
## 5.1 家长准备内容的工作流 | Parent Setup Workflow
text
中文：
1. 家长登录 → 进入“Parent Setup”面板
2. 选择视频文件（可选上传文字稿）
3. 点击“Upload Video”上传
4. 点击“Generate Summary”生成摘要
5. 预览生成的儿童友好总结和关键词
6. （可选）点击“Generate Voice”试听 TTS

English：
1. Parent logs in → enters “Parent Setup” panel
2. Selects video file (optional transcript upload)
3. Clicks “Upload Video” to upload
4. Clicks “Generate Summary” to generate summary
5. Previews the child-friendly summary and keywords
6. (Optional) Clicks “Generate Voice” to preview TTS
   
## 5.2 儿童学习的工作流 | Child Learning Workflow (Guided Session)
text
中文：
1. 家长切换到 Child Mode 或孩子自己进入“Child Learning”
2. 点击“Start Learning”开始引导式学习
3. 星辰朗读：无障碍描述 + 第一个问题
4. 孩子点击“Speak Answer”并说出答案
5. 系统识别并提交答案
6. 根据答案正确性：
   - 正确 → 正面反馈 + 下一题（回到步骤3）
   - 错误 → 鼓励 + 提示 + 重复当前问题
7. 学习完成后，家长可在“Learning Report”查看报告

English：
1. Parent switches to Child Mode OR child enters “Child Learning”
2. Clicks “Start Learning” to begin guided session
3. Xingchen reads: accessible description + first question
4. Child clicks “Speak Answer” and speaks the answer
5. System recognizes and submits the answer
6. Based on correctness:
   - Correct → positive feedback + next question (back to step 3)
   - Incorrect → encouragement + hint + repeat current question
7. After completion, parent can view the report in “Learning Report”

# 六，项目特色 / 卖点 | Key Features / Selling Points

✨ Starlight AI Learning Companion

专为视障儿童设计的语音优先学习伙伴。
A voice-first learning companion designed for visually impaired children.

🎧 视频学习 · 语音问答 · 智能识物 · 学习报告
Video Learning · Voice Q&A · Object Recognition · Learning Reports
🌟 星辰语音助手 + 可拖拽精灵陪伴
Xingchen Voice Assistant + Draggable Companion Sprite
🌌 宇宙深色主题 · 玻璃拟态 · 响应式设计
Deep Space Theme · Glassmorphism · Responsive Design

让每一个看不见的孩子，都能“听见”整个世界。
Let every child who cannot see “hear” the whole world.

#Accessibility #AIForGood #BlindChildren #EdTech

长推文 / 产品介绍 | Long Post / Product Introduction
让技术有温度：Starlight AI Learning Companion
Technology with Heart: Starlight AI Learning Companion

在看不见的世界里，声音是最好的桥梁。Starlight 是一款专为盲童设计的语音优先学习平台，让知识不再依赖于视觉。
In a world without sight, sound is the best bridge. Starlight is a voice-first learning platform designed for blind children, freeing knowledge from visual dependence.

### 🎓 核心能力 | Core Capabilities

视频上传 → 自动生成无障碍语音摘要 (Video upload → automatic accessible voice summary generation)

引导式学习 → 听问题 → 说答案 → 即时反馈 (Guided learning → listen → speak → instant feedback)

星辰语音助手 → 按钮录音 / 唤醒词持续监听 (Xingchen Voice Assistant → button recording / wake word listening)

智能识物系统 → YOLO 实时检测 + Coze 嵌入式识别 (Smart Object System → YOLO real-time detection + Coze embedded recognition)

家长报告 → 进度追踪 + 学习建议 (Parent Reports → progress tracking + learning suggestions)

### 🎨 设计亮点 | Design Highlights

深色宇宙主题（星空、银河、星云、流星）(Dark space theme: stars, Milky Way, nebula, shooting stars)

可拖拽、会互动的星辰精灵 (Draggable, interactive Xingchen sprite)

玻璃拟态卡片 + 滚动横幅 (Glassmorphism cards + marquee banner)

响应式布局，适配多端 (Responsive layout for multiple devices)

### 🔧 技术实现 | Technical Implementation

原生 HTML/CSS/JS，无框架依赖 (Vanilla HTML/CSS/JS, no framework dependencies)

Web Speech API 语音识别 (Web Speech API for voice recognition)

后端 TTS + 浏览器即时朗读双模式 (Backend TTS + browser instant speech dual mode)

纯 CSS 动态背景（非图片）(Pure CSS dynamic background, no images)

📌 项目已与 FastAPI 后端完成全功能联调，开箱即用。
The project is fully integrated with a FastAPI backend, ready to use out of the box.

成为黑暗世界里最亮的那颗星星。✨
Become the brightest star in a dark world.

# 七，项目结构 | Project Structure

.
├── 📁 backend_ai/                # 后端 AI 逻辑目录 (Backend AI Logic)
│   ├── 📁 __pycache__/           # Python 编译缓存 (Python Cache)
│   ├── 📁 outputs/               # 语音/数据输出结果 (Generated Outputs)
│   ├── 📁 uploads/               # 用户上传的原始视频/文件 (Uploaded Files)
│   ├── 📄 main.py                # 后端核心服务程序 (FastAPI/Flask Main Entry)
│   └── 📄 requirements.txt       # 后端依赖环境配置文件 (Backend Dependencies)
├── 📁 assets/                    # 静态资源（图片、图标、音频等） (Static Assets)
├── 📄 index.html                 # 项目主入口页面 (Main Landing Page)
├── 📄 camera.html                # 智能识物系统页面 (Smart Object System)
├── 📄 video.html                 # 视频魔法师功能页面 (AI Video Wizard Page)
├── 📄 api-client.js              # 后端 API 交互封装 (API Client Wrapper)
├── 📄 script.js                  # 前端全局核心逻辑 (Global Frontend Script)
├── 📄 style.css                  # 全局视觉样式表 (Global Stylesheet)
├── 📄 video-page.js              # 视频页面专用交互逻辑 (Video Page Logic)
├── 📄 legacy_feature.html        # 遗留功能备选页面 (Legacy Features)
└── 📄 blind-kids-xingchen-*.html # 系列功能迭代版本 (Iterative Versioned Pages)
    ├── galaxy-fixed-v9.html      # 银河稳定版
    ├── premium-v6.html           # 高级交互版
    └── sprite-v4.html            # 精灵助手版

# 八、部署方式 | Deployment
请根据实际环境补充以下内容。
Please complete the following based on your actual environment.

## 8.1 前置要求 | Prerequisites
后端服务：FastAPI 服务运行在 http://127.0.0.1:8000（可修改）
Backend service: FastAPI running at http://127.0.0.1:8000 (configurable)

YOLO 服务（可选）：物体检测后端运行在 http://127.0.0.1:8001（可修改）
YOLO service (optional): Object detection backend running at http://127.0.0.1:8001 (configurable)

DashScope API Key：需在服务端配置
DashScope API Key: Must be configured on the server side

## 🛠️ 环境安装 | Installation

创建并激活虚拟环境 (可选但推荐) Create and activate the virtual environment (optional but recommended)
```
python -m venv venv
.\venv\Scripts\activate
```
升级 pip 并安装依赖 Upgrade pip and install dependencies
```
python -m pip install --upgrade pip
pip install -r requirements.txt
```
克隆项目 | Clone the project

```
git clone [你的项目链接]
cd ~
```
配置后端 | Setup Backend

```
cd web/backend_ai
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

```
cd web
python -m http.server 5500
```

打开网页链接 Open the web link

http://127.0.0.1:5500/blind-kids-xingchen-galaxy-icons-v11-audio-fixed.html


# 联系我们  Connect us

Meihan.Liu23@student.xjtlu.edu.cn

# 致谢 Acknowledgments

本项目在开发过程中得到了多方的支持与帮助，特此致谢：

指导教师：感谢 [Antonio Garcia] 老师在无障碍设计思路及技术架构上提供的宝贵指导。

技术社区：感谢 OpenAI, Coze 以及 Edge-TTS 等开源项目及平台，为本项目提供了强大的 AI 能力支撑。

测试参与者：诚挚感谢参与用户测试的视障儿童及其家长，你们真实的反馈是我们不断优化的动力。

团队成员：感谢 ENT208 课程组全体成员的通力协作，共同完成了从概念到原型的跨越

This project received support and assistance from various parties during its development. We would like to express our gratitude for this: 
Supervisor: We would like to express our gratitude to [Antonio Garcia] for his invaluable guidance on the concepts and technical architecture of accessible design. 
Technical community: We would like to express our gratitude to the open-source projects and platforms such as OpenAI, Coze, and Edge-TTS for providing strong AI capabilities support for this project. 
Test participants: We sincerely thank the visually impaired children and their parents who participated in the user test. Your genuine feedback is the driving force for our continuous improvement. 
Team members: We would like to express our gratitude to all the members of the ENT208 course team for their collaborative efforts, which enabled us to successfully bridge the gap from concept to prototype.
