#version 300 es
precision mediump float;
in vec2 v_texcoord;
layout(location=0) out vec4 fragColor;
uniform sampler2D tex;
void main() {
    vec4 pixel = texture(tex, v_texcoord);
    vec3 color = pixel.rgb;
    float luminance = dot(color, vec3(0.2126, 0.7152, 0.0722));
    color = vec3(luminance);
    fragColor = vec4(color, pixel.a);
}
