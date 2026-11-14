// See-through glow for the first-person guide limbs (M5.8) and the flat colour of the coach window's arrow.
// URP version (M8.1, DEC-028): same look as the Built-in one; the visual rework is M8.4.
// Kept in Resources so it ships in builds; loaded by name in FirstPersonGuide.HologramMaterial.
//
// Exposed parameters:
//   _Color  Colour and base opacity (alpha) of the surface.
//   _Rim    Edge glow strength: adds opacity and a white tint where the surface turns away from the eye (0 = flat colour).
//   _Lines  Scan lines per metre, a faint vertical brightness ripple in world space (0 = none).
//   _ZTest  Depth test: 4 = LessEqual (hidden behind things), 8 = Always (drawn on top).
Shader "TheraQuest/Hologram"
{
    Properties
    {
        _Color ("Color", Color) = (0.35, 0.8, 1, 0.3)
        _Rim ("Edge glow (0 = flat colour)", Range(0, 3)) = 1.5
        _Lines ("Scan lines per metre (0 = none)", Float) = 70
        [Enum(UnityEngine.Rendering.CompareFunction)] _ZTest ("Depth test", Float) = 4
    }
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        Pass
        {
            Name "Hologram"
            Tags { "LightMode" = "UniversalForward" }
            Blend SrcAlpha OneMinusSrcAlpha
            ZWrite Off
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
                float _Lines;
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
                if (_Rim > 0)
                {
                    float3 view = normalize(GetCameraPositionWS() - i.positionWS);
                    float edge = 1 - saturate(abs(dot(normalize(i.normalWS), view)));
                    c.a = saturate(c.a + _Rim * edge * edge * edge);
                    c.rgb = lerp(c.rgb, half3(1, 1, 1), edge * edge * 0.5);
                }
                if (_Lines > 0) c.a *= 0.88 + 0.12 * sin(i.positionWS.y * _Lines * 6.2832);
                return c;
            }
            ENDHLSL
        }
    }
}
