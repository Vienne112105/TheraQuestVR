// Soft sunbeam through a window (M8.2): URP has no volumetric lighting, so each beam is a faint additive prism that is
// brightest at the window and fades toward the floor and toward its own edges. Static: no flicker, no motion (comfort).
//
// Exposed parameters:
//   _Color      Beam colour (warm white); alpha is ignored. Additive, so a dark colour is a faint beam.
//   _Intensity  Overall brightness multiplier (0 = invisible).
//   _EdgeSoft   How strongly the sides fade where the surface turns away from the eye (higher = softer sides).
Shader "TheraQuest/LightShaft"
{
    Properties
    {
        _Color ("Colour", Color) = (1, 0.88, 0.62, 1)
        _Intensity ("Intensity", Range(0, 1)) = 0.22
        _EdgeSoft ("Edge softness", Range(0.5, 4)) = 2
    }
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        Pass
        {
            Name "Shaft"
            Tags { "LightMode" = "UniversalForward" }
            Blend One One
            ZWrite Off
            ZTest LEqual
            Cull Off

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            CBUFFER_START(UnityPerMaterial)
                half4 _Color;
                half _Intensity;
                half _EdgeSoft;
            CBUFFER_END

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 normalWS : TEXCOORD0;
                float3 positionWS : TEXCOORD1;
                float2 uv : TEXCOORD2;
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
                o.uv = v.uv;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                // uv.y runs from the window (0) to the floor (1); uv.x across the beam
                half along = saturate(1 - i.uv.y);
                half across = 1 - abs(i.uv.x * 2 - 1);
                half edge = pow(saturate(abs(dot(normalize(i.normalWS), normalize(GetCameraPositionWS() - i.positionWS)))), _EdgeSoft);
                half a = along * along * smoothstep(0, 0.25, across) * edge * _Intensity;
                return half4(_Color.rgb * a, 1);
            }
            ENDHLSL
        }
    }
}
