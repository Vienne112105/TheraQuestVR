// Cartoon shading for the coach (human request 2026-10-27): flat colour lit in two tones with a hard-ish edge
// (cool shadow tint instead of grey), a soft rim light, and an outline drawn as a slightly inflated back-face
// shell. Built-in render pipeline (the project's current pipeline); works with single-pass stereo in a headset.
Shader "TheraQuest/Toon Outline"
{
    Properties
    {
        _Color ("Colour", Color) = (1, 1, 1, 1)
        _ShadeTint ("Shadow tint", Color) = (0.52, 0.58, 0.74, 1)
        _ShadeStep ("Light / shadow edge", Range(-1, 1)) = 0.25
        _ShadeSoft ("Edge softness", Range(0.001, 0.3)) = 0.04
        _RimColor ("Rim light (alpha = strength)", Color) = (1, 1, 1, 0.3)
        _RimPower ("Rim tightness", Range(1, 8)) = 4
        _OutlineColor ("Outline colour", Color) = (0.114, 0.208, 0.341, 1)
        _OutlineWidth ("Outline width (metres)", Range(0, 0.02)) = 0.008
    }

    SubShader
    {
        Tags { "RenderType" = "Opaque" "Queue" = "Geometry" }

        CGPROGRAM
        #pragma surface surf Toon fullforwardshadows
        #pragma target 3.0

        fixed4 _Color, _ShadeTint, _RimColor;
        half _ShadeStep, _ShadeSoft, _RimPower;

        struct Input { float3 viewDir; };

        half4 LightingToon(SurfaceOutput s, half3 lightDir, half atten)
        {
            half ndl = dot(s.Normal, lightDir);
            // Two tones: lit or shadowed (including cast shadows), with a narrow soft edge between them
            half lit = smoothstep(_ShadeStep - _ShadeSoft, _ShadeStep + _ShadeSoft, ndl);
            #ifdef UNITY_PASS_FORWARDADD
                half3 light = _LightColor0.rgb * lit * atten;   // extra lights only add where they reach
            #else
                lit *= smoothstep(0.3, 0.7, atten);
                half3 light = _LightColor0.rgb * lerp(_ShadeTint.rgb, 1, lit);
            #endif
            return half4(s.Albedo * light, s.Alpha);
        }

        void surf(Input IN, inout SurfaceOutput o)
        {
            o.Albedo = _Color.rgb;
            o.Alpha = 1;
            half rim = pow(1 - saturate(dot(normalize(IN.viewDir), o.Normal)), _RimPower);
            o.Emission = _RimColor.rgb * _RimColor.a * rim;
        }
        ENDCG

        Pass
        {
            Name "OUTLINE"
            Cull Front
            ZWrite On

            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_fog
            #pragma multi_compile_instancing
            #include "UnityCG.cginc"

            fixed4 _OutlineColor;
            float _OutlineWidth;

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                UNITY_FOG_COORDS(0)
                UNITY_VERTEX_OUTPUT_STEREO
            };

            v2f vert(appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_OUTPUT(v2f, o);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                // Push each vertex out along its normal by a fixed distance in the world, so the outline is
                // the same thickness on every coach whatever its import scale
                float3 world = mul(unity_ObjectToWorld, v.vertex).xyz;
                world += normalize(UnityObjectToWorldNormal(v.normal)) * _OutlineWidth;
                o.pos = UnityWorldToClipPos(world);
                UNITY_TRANSFER_FOG(o, o.pos);
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 c = _OutlineColor;
                UNITY_APPLY_FOG(i.fogCoord, c);
                return c;
            }
            ENDCG
        }
    }
    FallBack "Diffuse"
}
