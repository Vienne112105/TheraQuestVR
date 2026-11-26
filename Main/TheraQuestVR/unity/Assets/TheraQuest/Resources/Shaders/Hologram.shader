// See-through glow for the first-person guide limbs (M5.8) and the solid colour of the coach window's arrow.
// URP HLSL (M8.1, DEC-028); reworked look in M8.4: tinted fresnel rim, soft inner fill, steady glow inside tolerance.
// Kept in Resources so it ships in builds; loaded by name in FirstPersonGuide.HologramMaterial.
//
// Exposed parameters (all set from code, see FirstPersonGuide.HologramMaterial and HologramLook):
//   _Color     Fill colour; alpha is the opacity of the limb's middle (the part that faces the eye).
//   _Rim       Edge (fresnel) strength: adds opacity where the surface turns away from the eye. 0 = flat colour.
//   _RimPower  How tight the edge is: higher keeps the rim to a thin outline, lower spreads it over the limb.
//   _RimTint   How far the edge colour moves from the fill colour toward white (0 = same colour, 1 = white).
//   _Glow      0 to 1, set by HologramLook only while the evaluator reports the angle inside tolerance. Brightens
//              the rim and fill past 1 (HDR), so the room's light bloom gives a soft halo. Eased in, never pulsed.
//   _GlowBoost How bright full glow is: the colour is multiplied by 1 + _Glow * _GlowBoost (on the rim, half on the fill).
//   _Lines     Scan lines per metre, a faint vertical brightness ripple in world space (0 = none, the default).
//   _Cutoff    Alpha clip: pixels fainter than this are discarded (nothing visible is lost; skips blending them).
//   _ZTest     Depth test: 4 = LessEqual (hidden behind things), 8 = Always (drawn on top).
//   _SrcBlend, _DstBlend, _ZWrite  Blend mode. See-through limbs: SrcAlpha / OneMinusSrcAlpha / 0 (they must stay
//              alpha-blended: the patient sees the room through them). Solid (the arrow): One / Zero / 1, no blending.
//
// Cost: one pass, no textures, about 20 ALU per pixel. Frame Debugger (M8.4, laptop and headset renderers): the six
// limb capsules draw in DrawTransparentObjects as one SRP-batched step (6 draw calls, 3300 vertices) into the HDR
// camera target, so the glow reaches the bloom; the solid arrow draws in the coach window camera (50 vertices each).
Shader "TheraQuest/Hologram"
{
    Properties
    {
        _Color ("Fill colour (alpha = middle opacity)", Color) = (0.15, 0.49, 0.63, 0.32)
        _Rim ("Edge glow (0 = flat colour)", Range(0, 3)) = 1.5
        _RimPower ("Edge tightness", Range(1, 8)) = 2.2
        _RimTint ("Edge colour toward white", Range(0, 1)) = 0.2
        _Glow ("Glow inside tolerance (set by code)", Range(0, 1)) = 0
        _GlowBoost ("Glow brightness", Range(0, 3)) = 0.6
        _Lines ("Scan lines per metre (0 = none)", Float) = 0
        _Cutoff ("Alpha clip threshold", Range(0, 0.2)) = 0.02
        [Enum(UnityEngine.Rendering.CompareFunction)] _ZTest ("Depth test", Float) = 4
        [Enum(UnityEngine.Rendering.BlendMode)] _SrcBlend ("Source blend", Float) = 5
        [Enum(UnityEngine.Rendering.BlendMode)] _DstBlend ("Destination blend", Float) = 10
        [Toggle] _ZWrite ("Depth write", Float) = 0
    }
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        Pass
        {
            Name "Hologram"
            Tags { "LightMode" = "UniversalForward" }
            Blend [_SrcBlend] [_DstBlend]
            ZWrite [_ZWrite]
            ZTest [_ZTest]
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                float _Rim;
                float _RimPower;
                float _RimTint;
                float _Glow;
                float _GlowBoost;
                float _Lines;
                float _Cutoff;
            CBUFFER_END

            struct Attributes
            {
                float4 positionOS : POSITION;
                float3 normalOS : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 normalWS : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                half4 c = _Color;
                half edge = 0;
                if (_Rim > 0)
                {
                    float3 view = normalize(GetCameraPositionWS() - i.positionWS);
                    edge = pow(1 - saturate(abs(dot(normalize(i.normalWS), view))), _RimPower);
                    // Soft fill: the middle keeps the fill alpha, the edge adds opacity and lightens toward white
                    c.a = saturate(c.a + _Rim * edge);
                    c.rgb = lerp(c.rgb, half3(1, 1, 1), edge * _RimTint);
                }
                // Steady glow (no time term): brighter rim, a little brighter fill, a little more opaque
                c.rgb *= 1 + _Glow * _GlowBoost * (0.5 + edge);
                c.a = saturate(c.a + _Glow * 0.12);
                if (_Lines > 0) c.a *= 0.88 + 0.12 * sin(i.positionWS.y * _Lines * 6.2832);
                clip(c.a - _Cutoff);
                return c;
            }
            ENDHLSL
        }
    }
}
