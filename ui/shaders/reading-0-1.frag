#version 300 es
precision mediump float;
in vec2 v_texcoord;
layout(location=0) out vec4 fragColor;
uniform sampler2D tex;
void main() {
    vec4 pixel = texture(tex, v_texcoord);
    vec3 color = pixel.rgb;
    color *= vec3(1.0, 0.88, 0.66);
    fragColor = vec4(color, pixel.a);
}
