# Custom 3D Coach Avatars

Extra coaches now go in `Assets/TheraQuest/Resources/Coaches/` (one sub-folder per model, e.g. `Resources/Coaches/Man002_FBX/Male_002.fbx`).
Every Humanoid model found there is added to the coach menu automatically (its file name is the menu name), after the Female and Male coaches.
The notes below still apply to the model's Import Settings; no scene setup is needed.

(Older note:) Drop your 3D humanoid character models (FBX, OBJ, or GLB) into this folder.

### Supported Avatar Sources
- **Adobe Mixamo** (https://www.mixamo.com/): Download characters like *Remy*, *Michelle*, *Y Bot*, or *Malcolm* (T-Pose or standard rest pose).
- **Ready Player Me** (https://readyplayer.me/): Export custom stylized or realistic avatars as FBX/GLB.
- **VRoid Studio** or Unity Asset Store humanoid characters.

### Unity Setup Steps
1. Place the character file (e.g., `Therapist_Maya.fbx`) and its texture folder here.
2. Select the model in the Project window and inspect its **Import Settings**:
   - Go to the **Rig** tab.
   - Set **Animation Type** to **Humanoid**.
   - Click **Apply**.
3. Select the `Session` or `Coach` GameObject in the scene (which has the `HumanoidCoach` script).
4. In the Inspector under **Characters**:
   - Increase the size by 1.
   - Enter a display name (e.g., "Dr. Maya").
   - Drag your imported model prefab into the **Model** slot.
5. In Play mode, your 3D avatar will automatically take over from the capsule figure!
