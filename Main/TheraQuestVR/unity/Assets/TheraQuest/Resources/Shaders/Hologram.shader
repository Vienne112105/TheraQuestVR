// See-through glow for the first-person guide limbs (M5.8) and the flat colour of the coach window's arrow.
// Kept in Resources so it ships in builds; loaded by name in FirstPersonGuide.HologramMaterial.
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
        Tags { "Queue" = "Transparent" "RenderType" = "Transparent" "IgnoreProjector" = "True" }
        Blend SrcAlpha OneMinusSrcAlpha
        ZWrite Off
        ZTest [_ZTest]
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"

            fixed4 _Color;
            float _Rim, _Lines;

            struct appdata
            {
                float4 vertex : POSITION;
                float3 normal : NORMAL;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct v2f
            {
                float4 pos : SV_POSITION;
                float3 normal : TEXCOORD0;
                float3 world : TEXCOORD1;
                UNITY_VERTEX_OUTPUT_STEREO
            };

            v2f vert(appdata v)
            {
                v2f o;
                UNITY_SETUP_INSTANCE_ID(v);
                UNITY_INITIALIZE_VERTEX_OUTPUT_STEREO(o);
                o.pos = UnityObjectToClipPos(v.vertex);
                o.normal = UnityObjectToWorldNormal(v.normal);
                o.world = mul(unity_ObjectToWorld, v.vertex).xyz;
                return o;
            }

            fixed4 frag(v2f i) : SV_Target
            {
                fixed4 c = _Color;
                if (_Rim > 0)
                {
                    float3 view = normalize(_WorldSpaceCameraPos - i.world);
                    float edge = 1 - saturate(abs(dot(normalize(i.normal), view)));
                    c.a = saturate(c.a + _Rim * edge * edge * edge);
                    c.rgb = lerp(c.rgb, 1, edge * edge * 0.5);
                }
                if (_Lines > 0) c.a *= 0.88 + 0.12 * sin(i.world.y * _Lines * 6.2832);
                return c;
            }
            ENDCG
        }
    }
}
