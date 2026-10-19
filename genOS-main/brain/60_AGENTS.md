# AI Workforce

Authoritative source of truth for the project's AI workforce.
AI-maintained. See `integrations/agency_agents.md` for the selection protocol.

This file tracks which specialist agents are active, deferred, or removed for this project.

## Core Agents
- **`engineering-ai-engineer`** (`.agents/skills/engineering-ai-engineer`)
  - *Role:* AI and Computer Vision Engineer
  - *Purpose:* Owns Python OpenCV and MediaPipe Pose estimation pipelines, 2D/3D joint angle math, coordinate transformations, and UDP streaming to Unity.
- **`unity-architect`** (`.agents/skills/unity-architect`)
  - *Role:* Senior Unity Engine Architect
  - *Purpose:* Owns data-driven modularity, ScriptableObject architecture, component lifecycle, memory management, and anti-pattern prevention.
- **`xr-interface-architect`** (`.agents/skills/xr-interface-architect`)
  - *Role:* Spatial VR Interaction Designer
  - *Purpose:* Owns dual-mode HUD layout (Patient vs Therapist), ergonomics, comfortable field-of-view positioning, and System Usability Scale (SUS) compliance.
- **`engineering-data-engineer`** (`.agents/skills/engineering-data-engineer`)
  - *Role:* Clinical Data & Backend Engineer
  - *Purpose:* Owns relational SQLite schemas, clinical protocol persistence, adherence calculations, and session telemetry endpoints.

## Milestone Agents (Active for M1 — Exercise Library & Avatar Guidance)
- **`unity-editor-tool-developer`** (`.agents/skills/unity-editor-tool-developer`)
  - *Role:* Unity Workflow & Tool Automation Developer
  - *Purpose:* Implements custom Inspector tools, asset postprocessors, and scene building tools (`TheraQuestSceneBuilder.cs`, `CoachModelImporter.cs`) for adding new exercises and avatars.
- **`game-designer`** (`.agents/skills/game-designer`)
  - *Role:* Gameplay & Gamification Designer
  - *Purpose:* Balances repetition scoring curves, combo multipliers, hold countdown pacing, and Flow Theory dynamics.
- **`game-audio-engineer`** (`.agents/skills/game-audio-engineer`)
  - *Role:* Game Audio & Sound Engineer
  - *Purpose:* Implements audio cues, exercise rhythm metronomes, feedback chimes, and accessibility audio captioning.

## Optional Specialists
- **`testing-reality-checker`** (`.agents/skills/testing-reality-checker`)
  - *Role:* Mathematical Evaluation & Benchmark Specialist
  - *Purpose:* Reserved primarily for Milestone M2 to evaluate Confusion Matrices (Accuracy ≥85%, Precision ≥80%, Recall ≥80%, F1 ≥80%) and Mean Absolute Angle Error against goniometric baselines.
- **`level-designer`** (`.agents/skills/level-designer`)
  - *Role:* 3D Clinic Environment Designer
  - *Purpose:* Designs procedural clinic layout, spatial flow, rehabilitation examination areas, and URP lighting.
- **`unity-shader-graph-artist`** (`.agents/skills/unity-shader-graph-artist`)
  - *Role:* Technical Artist & URP Shader Specialist
  - *Purpose:* Implements VR visual feedback effects, target zone hold shaders, and Meta Quest GPU fill rate optimization.

## Milestone Agents (Active for M4 — Foundation Hardening)
- **`security-auditor`**
  - *Role:* Application Security Specialist
  - *Purpose:* Reviews M4.2 backend and dashboard fixes (path containment, XSS, credentials, token storage, CORS) and the M4.3 VR client trust boundary.
- **`testing-reality-checker`** (`.agents/skills/testing-reality-checker`)
  - *Purpose (M4):* Checks M4.5 so evaluation metrics come only from real, labelled inputs and synthetic output is clearly marked (DEC-011).

## Deferred Agents
- none

## Removed / Excluded Agents
- Cloud-native microservice architects (Kubernetes, AWS Lambda), mobile app developers (iOS/Android native), and multi-tenant e-commerce billing specialists — excluded as out of scope for a local-first PC VR clinic system.

## Workforce Rationale
The selected 10 specialists match the interdisciplinary nature of TheraQuest VR: computer vision tracking, Unity 6 VR development, gamification design, biomechanical analysis, clinical data pipelines, and academic research evaluation.

## Last Workforce Review
- **Date:** 2026-10-20
- **Milestone:** M4 kickoff (security-auditor activated; testing-reality-checker assigned to M4.5)
