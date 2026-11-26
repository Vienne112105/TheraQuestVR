// Surface detail for the room's flat-colour 3D models (M8.2): a fine grain (wood streaks, fabric weave, brushed metal
// or soft speckle) and a slow patchy variation, both projected from the world onto the model (triplanar), so the
// models need no UVs. The grain also varies the shininess, which removes the flat plastic look.
// URP lit shader (DEC-028), made at runtime by PropDetail.Apply from each model material's colour.
//
// Exposed parameters:
//   _BaseColor      Colour of the surface (copied from the model's own material).
//   _GrainTex       Tileable grey grain picture (0.5 = no change).
//   _GrainScale     Grain repeats per metre.
//   _GrainStrength  How much the grain lightens and darkens the colour (0 = flat colour, 0.5 = strong).
//   _MacroStrength  How much slow, large patches vary the colour (0 = none).
//   _Smoothness     Average shininess (0 = matte, 1 = mirror).
//   _SmoothVar      How much the grain varies the shininess around the average.
//   _Metallic       0 = non-metal, 1 = metal.
Shader "TheraQuest/PropDetail"
{
    Properties
    {
        _BaseColor ("Colour", Color) = (0.7, 0.7, 0.7, 1)
        _GrainTex ("Grain (grey, tileable)", 2D) = "grey" {}
        _GrainScale ("Grain repeats per metre", Range(0.5, 40)) = 6
        _GrainStrength ("Grain strength", Range(0, 0.6)) = 0.3
        _MacroStrength ("Patch strength", Range(0, 0.4)) = 0.12
        _Smoothness ("Smoothness", Range(0, 1)) = 0.3
        _SmoothVar ("Smoothness variation", Range(0, 0.5)) = 0.12
        _Metallic ("Metallic", Range(0, 1)) = 0
    }
    SubShader
    {
        Tags { "RenderPipeline" = "UniversalPipeline" "RenderType" = "Opaque" "Queue" = "Geometry" }

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode" = "UniversalForward" }
            ZWrite On
            Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag

            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE _MAIN_LIGHT_SHADOWS_SCREEN
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ EVALUATE_SH_MIXED EVALUATE_SH_VERTEX
            #pragma multi_compile_fragment _ _ADDITIONAL_LIGHT_SHADOWS
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BLENDING
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_BOX_PROJECTION
            #pragma multi_compile_fragment _ _REFLECTION_PROBE_ATLAS
            #pragma multi_compile_fragment _ _SHADOWS_SOFT _SHADOWS_SOFT_LOW _SHADOWS_SOFT_MEDIUM _SHADOWS_SOFT_HIGH
            #pragma multi_compile_fragment _ _SCREEN_SPACE_OCCLUSION
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #include_with_pragmas "Packages/com.unity.render-pipelines.core/ShaderLibrary/FoveatedRenderingKeywords.hlsl"
            #pragma multi_compile_fragment _ _LIGHT_COOKIES
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            TEXTURE2D(_GrainTex);
            SAMPLER(sampler_GrainTex);

            CBUFFER_START(UnityPerMaterial)
                half4 _BaseColor;
                float4 _GrainTex_ST;
                float _GrainScale;
                half _GrainStrength;
                half _MacroStrength;
                half _Smoothness;
                half _SmoothVar;
                half _Metallic;
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
                float3 positionWS : TEXCOORD0;
                half3 normalWS : TEXCOORD1;
                UNITY_VERTEX_INPUT_INSTANCE_ID
                UNITY_VERTEX_OUTPUT_STEREO
            };

            Varyings vert(Attributes v)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_TRANSFER_INSTANCE_ID(v, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.positionWS = TransformObjectToWorld(v.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(o.positionWS);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                return o;
            }

            // Grey value of the grain projected along the three axes, blended by the surface direction.
            half Triplanar(float3 p, half3 n, float scale)
            {
                half3 w = pow(abs(n), 4);
                w /= (w.x + w.y + w.z + 1e-5);
                half gx = SAMPLE_TEXTURE2D(_GrainTex, sampler_GrainTex, p.zy * scale).r;
                half gy = SAMPLE_TEXTURE2D(_GrainTex, sampler_GrainTex, p.xz * scale).r;
                half gz = SAMPLE_TEXTURE2D(_GrainTex, sampler_GrainTex, p.xy * scale).r;
                return gx * w.x + gy * w.y + gz * w.z;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                UNITY_SETUP_STEREO_EYE_INDEX_POST_VERTEX(i);

                half3 n = normalize(i.normalWS);
                half grain = Triplanar(i.positionWS, n, _GrainScale) - 0.5h;
                half macro = Triplanar(i.positionWS + 17.3, n, _GrainScale * 0.12) - 0.5h;

                SurfaceData s = (SurfaceData)0;
                // Multiplicative variation, plus a small additive part so near-black surfaces (dumbbells) show it too
                half3 varied = _BaseColor.rgb * (1 + 2 * _GrainStrength * grain + 2 * _MacroStrength * macro)
                             + 0.35h * _GrainStrength * grain + 0.25h * _MacroStrength * macro;
                s.albedo = saturate(varied + 0.03h * _GrainStrength * 2);
                s.metallic = _Metallic;
                s.smoothness = saturate(_Smoothness + 2 * _SmoothVar * grain);
                s.occlusion = 1;
                s.alpha = 1;
                s.normalTS = half3(0, 0, 1);

                InputData d = (InputData)0;
                d.positionWS = i.positionWS;
                d.positionCS = i.positionCS;
                d.normalWS = n;
                d.viewDirectionWS = GetWorldSpaceNormalizeViewDir(i.positionWS);
                d.shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                d.bakedGI = SampleSH(n);
                d.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                d.shadowMask = half4(1, 1, 1, 1);

                return UniversalFragmentPBR(d, s);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode" = "ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0
            Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                float3 positionWS = TransformObjectToWorld(v.positionOS.xyz);
                float3 normalWS = TransformObjectToWorldNormal(v.normalOS);
            #if _CASTING_PUNCTUAL_LIGHT_SHADOW
                float3 lightDir = normalize(_LightPosition - positionWS);
            #else
                float3 lightDir = _LightDirection;
            #endif
                o.positionCS = TransformWorldToHClip(ApplyShadowBias(positionWS, normalWS, lightDir));
                o.positionCS = ApplyShadowClamping(o.positionCS);
                return o;
            }

            half4 frag(Varyings i) : SV_Target { return 0; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode" = "DepthOnly" }
            ZWrite On
            ColorMask R
            Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes { float4 positionOS : POSITION; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                return o;
            }

            half frag(Varyings i) : SV_Target { return i.positionCS.z; }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode" = "DepthNormals" }
            ZWrite On
            Cull Back

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes { float4 positionOS : POSITION; float3 normalOS : NORMAL; UNITY_VERTEX_INPUT_INSTANCE_ID };
            struct Varyings { float4 positionCS : SV_POSITION; half3 normalWS : TEXCOORD0; };

            Varyings vert(Attributes v)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(v);
                o.positionCS = TransformObjectToHClip(v.positionOS.xyz);
                o.normalWS = TransformObjectToWorldNormal(v.normalOS);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                return half4(NormalizeNormalPerPixel(i.normalWS), 0);
            }
            ENDHLSL
        }
    }
}
