// fb_panel.c — Versão em C do seu script Python para desenhar em /dev/fbX
// ----------------------------------------------------------------------
// Requisitos (header-only):
//   - stb_image.h       -> https://github.com/nothings/stb (para carregar PNG/JPG)
//   - stb_truetype.h    -> https://github.com/nothings/stb (para renderizar TTF)
// Instale também uma fonte TTF no sistema (ex.: DejaVuSans e DejaVuSans-Bold)
// Coloque os headers no mesmo diretório do código ou em um include path do seu projeto.
//
// Compilação (exemplos):
//   gcc -O2 -Wall -Wextra fb_panel.c -o fb_panel -lm
// Execução:
//   sudo ./fb_panel
//
// Observações:
// - Desenha diretamente no framebuffer (fbdev) sem X11/Wayland.
// - Suporta RGB565 (com conversão) e RGB24/32.
// - Renderiza hora/data e um PNG com alpha blending (canto inferior direito por padrão).
// - Rotação suportada: 0, 90, 180, 270.
// - Ajuste os paths de fonte/PNG conforme seu sistema.

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <stdarg.h>
#include <time.h>
#include <string.h>
#include <unistd.h>
#include <fcntl.h>
#include <dirent.h>
#include <glob.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <errno.h>
#include <math.h>

// ====== STB headers (coloque os .h no projeto) ======
#define STB_IMAGE_IMPLEMENTATION
#include "stb_image.h"
#define STB_TRUETYPE_IMPLEMENTATION
#include "stb_truetype.h"
// ====================================================

// ================= Configurações =====================
static const char *TARGET_FB_NAME = "fb_ili9486"; // Nome exposto em /sys/class/graphics/fb*/name
static const char *IMG_PATH       = "/home/dw/painel/kakashicute.png"; // PNG com alpha
static const char *FONT_BOLD_TTF  = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf";
static const char *FONT_REG_TTF   = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf";
static const int   FONT_BIG_PX    = 28;
static const int   FONT_SMALL_PX  = 22;
static const int   ROTATE_DEG     = 0;   // 0, 90, 180, 270
static const char *TITLE_TEXT     = "DOGLAS WICHT";
// ====================================================

// Util: leitura simples de arquivo texto
static bool read_text_file(const char *path, char *buf, size_t bufsz) {
    FILE *f = fopen(path, "r");
    if (!f) return false;
    size_t n = fread(buf, 1, bufsz - 1, f);
    fclose(f);
    if (n == 0) return false;
    buf[n] = '\0';
    return true;
}

// Encontra "/dev/fbX" cujo /sys/class/graphics/fbX/name == TARGET_FB_NAME
static bool find_fb_by_name(const char *target, char *out_dev, size_t out_sz, int *out_index) {
    glob_t g = {0};
    if (glob("/sys/class/graphics/fb*/name", 0, NULL, &g) != 0) return false;
    bool ok = false;
    for (size_t i = 0; i < g.gl_pathc; i++) {
        char namebuf[128];
        if (!read_text_file(g.gl_pathv[i], namebuf, sizeof(namebuf))) continue;
        // trim
        for (char *p = namebuf; *p; ++p) if (*p=='\n' || *p=='\r') *p='\0';
        if (strcmp(namebuf, target) == 0) {
            // path example: /sys/class/graphics/fb2/name
            char *slash = strrchr(g.gl_pathv[i], '/');
            if (!slash) continue;
            char fbdir[256];
            strncpy(fbdir, g.gl_pathv[i], slash - g.gl_pathv[i]);
            fbdir[slash - g.gl_pathv[i]]='\0'; // -> /sys/class/graphics/fb2
            int idx = -1;
            if (sscanf(fbdir, "/sys/class/graphics/fb%d", &idx) == 1) {
                snprintf(out_dev, out_sz, "/dev/fb%d", idx);
                if (out_index) *out_index = idx;
                ok = true;
                break;
            }
        }
    }
    globfree(&g);
    return ok;
}

static bool read_virtual_size(int fb_index, int *w, int *h) {
    char path[256];
    snprintf(path, sizeof(path), "/sys/class/graphics/fb%d/virtual_size", fb_index);
    char buf[128];
    if (!read_text_file(path, buf, sizeof(buf))) return false;
    int ww=0, hh=0;
    if (sscanf(buf, "%d,%d", &ww, &hh) == 2) { *w = ww; *h = hh; return true; }
    return false;
}

static int read_int_file(const char *path, int defval) {
    char buf[128];
    if (!read_text_file(path, buf, sizeof(buf))) return defval;
    int v=defval; sscanf(buf, "%d", &v); return v;
}

// Framebuffer em memória (RGB888)
typedef struct { int w, h; uint8_t *pix; } Surface;

static Surface surface_make(int w, int h) {
    Surface s = { w, h, NULL };
    s.pix = (uint8_t*)calloc((size_t)w * h * 3, 1);
    return s;
}

static void surface_free(Surface *s) {
    free(s->pix); s->pix=NULL; s->w=s->h=0;
}

// Set pixel RGB na surface (clamped)
static inline void put_rgb(Surface *s, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    if ((unsigned)x >= (unsigned)s->w || (unsigned)y >= (unsigned)s->h) return;
    size_t idx = ((size_t)y * s->w + x) * 3;
    s->pix[idx+0] = r; s->pix[idx+1] = g; s->pix[idx+2] = b;
}

static inline void blend_rgba_over(Surface *s, int x, int y, uint8_t r, uint8_t g, uint8_t b, uint8_t a) {
    if ((unsigned)x >= (unsigned)s->w || (unsigned)y >= (unsigned)s->h) return;
    size_t idx = ((size_t)y * s->w + x) * 3;
    float alpha = a / 255.0f;
    s->pix[idx+0] = (uint8_t)(r * alpha + s->pix[idx+0] * (1.0f - alpha));
    s->pix[idx+1] = (uint8_t)(g * alpha + s->pix[idx+1] * (1.0f - alpha));
    s->pix[idx+2] = (uint8_t)(b * alpha + s->pix[idx+2] * (1.0f - alpha));
}

// Desenha retângulo sólido
static void fill_rect(Surface *s, int x, int y, int w, int h, uint8_t r, uint8_t g, uint8_t b) {
    if (w<=0||h<=0) return;
    int x0 = x<0?0:x, y0 = y<0?0:y;
    int x1 = x+w; if (x1>s->w) x1=s->w;
    int y1 = y+h; if (y1>s->h) y1=s->h;
    for (int yy=y0; yy<y1; ++yy) {
        for (int xx=x0; xx<x1; ++xx) {
            put_rgb(s, xx, yy, r, g, b);
        }
    }
}

// Carrega PNG/JPG (RGBA) e faz downscale se necessário (thumbnail-like)
static unsigned char* load_image_rgba(const char *path, int *w, int *h) {
    int n=0; // canais
    stbi_uc *data = stbi_load(path, w, h, &n, 4);
    return data; // caller deve stbi_image_free
}

// Paste RGBA com alpha
static void blit_rgba(Surface *dst, int dx, int dy, const unsigned char *src, int sw, int sh) {
    for (int y=0; y<sh; ++y) {
        for (int x=0; x<sw; ++x) {
            const unsigned char *p = src + (y*sw + x)*4;
            blend_rgba_over(dst, dx+x, dy+y, p[0], p[1], p[2], p[3]);
        }
    }
}

// Rotaciona (0/90/180/270) — retorna nova Surface (caller free)
static Surface rotate_surface(const Surface *s, int deg) {
    if (deg == 0) {
        Surface out = surface_make(s->w, s->h);
        memcpy(out.pix, s->pix, (size_t)s->w*s->h*3);
        return out;
    } else if (deg == 90) {
        Surface out = surface_make(s->h, s->w);
        for (int y=0; y<s->h; ++y)
            for (int x=0; x<s->w; ++x) {
                size_t si = ((size_t)y*s->w + x)*3;
                int nx = s->h - 1 - y, ny = x;
                size_t di = ((size_t)ny*out.w + nx)*3;
                out.pix[di+0]=s->pix[si+0]; out.pix[di+1]=s->pix[si+1]; out.pix[di+2]=s->pix[si+2];
            }
        return out;
    } else if (deg == 180) {
        Surface out = surface_make(s->w, s->h);
        for (int y=0; y<s->h; ++y)
            for (int x=0; x<s->w; ++x) {
                size_t si = ((size_t)y*s->w + x)*3;
                int nx = s->w - 1 - x, ny = s->h - 1 - y;
                size_t di = ((size_t)ny*out.w + nx)*3;
                out.pix[di+0]=s->pix[si+0]; out.pix[di+1]=s->pix[si+1]; out.pix[di+2]=s->pix[si+2];
            }
        return out;
    } else if (deg == 270) {
        Surface out = surface_make(s->h, s->w);
        for (int y=0; y<s->h; ++y)
            for (int x=0; x<s->w; ++x) {
                size_t si = ((size_t)y*s->w + x)*3;
                int nx = y, ny = s->w - 1 - x;
                size_t di = ((size_t)ny*out.w + nx)*3;
                out.pix[di+0]=s->pix[si+0]; out.pix[di+1]=s->pix[si+1]; out.pix[di+2]=s->pix[si+2];
            }
        return out;
    }
    // default
    Surface out = surface_make(s->w, s->h);
    memcpy(out.pix, s->pix, (size_t)s->w*s->h*3);
    return out;
}

// ===== Texto com stb_truetype =====
typedef struct {
    stbtt_fontinfo font;
    unsigned char *ttf_data;
} Font;

static bool font_load(Font *F, const char *ttf_path) {
    memset(F, 0, sizeof(*F));
    FILE *fp = fopen(ttf_path, "rb");
    if (!fp) return false;
    fseek(fp, 0, SEEK_END);
    long sz = ftell(fp);
    fseek(fp, 0, SEEK_SET);
    F->ttf_data = (unsigned char*)malloc(sz);
    if (!F->ttf_data) { fclose(fp); return false; }
    if (fread(F->ttf_data, 1, sz, fp) != (size_t)sz) { fclose(fp); free(F->ttf_data); return false; }
    fclose(fp);
    if (!stbtt_InitFont(&F->font, F->ttf_data, stbtt_GetFontOffsetForIndex(F->ttf_data,0))) {
        free(F->ttf_data); F->ttf_data=NULL; return false;
    }
    return true;
}

static void font_free(Font *F) {
    free(F->ttf_data); F->ttf_data=NULL;
}

static void draw_text(Surface *s, Font *F, float px, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    float scale = stbtt_ScaleForPixelHeight(&F->font, px);
    int ascent, descent, lineGap; stbtt_GetFontVMetrics(&F->font, &ascent, &descent, &lineGap);
    int baseline = (int)(ascent * scale);

    int pen_x = x;
    int pen_y = y + baseline;

    for (const char *p = (const char*)F; (void)p, 0; ) break; // quiet unused warning pattern

    // Texto simples sem UTF-8 complexo (assume ASCII/latin básico)
    // Para acentos/UTF-8, seria necessário decodificar e mapear codepoints.
    const char *str = TITLE_TEXT; // placeholder para assinatura da função
    (void)str; // evitamos warning, função abaixo tem overload com string
}

static void draw_text_string(Surface *s, Font *F, const char *text, float px, int x, int y, uint8_t r, uint8_t g, uint8_t b) {
    float scale = stbtt_ScaleForPixelHeight(&F->font, px);
    int ascent, descent, lineGap; stbtt_GetFontVMetrics(&F->font, &ascent, &descent, &lineGap);
    int baseline = (int)(ascent * scale);
    int pen_x = x;
    int pen_y = y + baseline;

    for (const char *c = text; *c; ++c) {
        int ch = (unsigned char)(*c);
        int ax, lsb; stbtt_GetCodepointHMetrics(&F->font, ch, &ax, &lsb);
        int cx0, cy0, cx1, cy1; stbtt_GetCodepointBitmapBox(&F->font, ch, scale, scale, &cx0, &cy0, &cx1, &cy1);
        int gw = cx1 - cx0, gh = cy1 - cy0;
        unsigned char *bitmap = (unsigned char*)malloc((size_t)gw*gh);
        if (bitmap) {
            stbtt_MakeCodepointBitmap(&F->font, bitmap, gw, gh, gw, scale, scale, ch);
            for (int yy=0; yy<gh; ++yy) {
                for (int xx=0; xx<gw; ++xx) {
                    uint8_t a = bitmap[yy*gw + xx];
                    blend_rgba_over(s, pen_x + cx0 + xx, pen_y + cy0 + yy, r, g, b, a);
                }
            }
            free(bitmap);
        }
        int kern = (int)(scale * stbtt_GetCodepointKernAdvance(&F->font, ch, (unsigned char)*(c+1)));
        pen_x += (int)(ax * scale) + kern;
    }
}

// Converte RGB888 -> RGB565 (LSB primeiro como no Python: out[0]=LSB, out[1]=MSB)
static void write_to_fb_rgb565(int fbfd, const Surface *s) {
    size_t total_bytes = (size_t)s->w * s->h * 2;
    uint8_t *line = (uint8_t*)malloc((size_t)s->w * 2);
    if (!line) return;
    for (int y=0; y<s->h; ++y) {
        for (int x=0; x<s->w; ++x) {
            size_t si = ((size_t)y * s->w + x) * 3;
            uint8_t R = s->pix[si+0], G = s->pix[si+1], B = s->pix[si+2];
            uint16_t r = (uint16_t)(R >> 3);
            uint16_t g = (uint16_t)(G >> 2);
            uint16_t b = (uint16_t)(B >> 3);
            uint16_t rgb565 = (uint16_t)((r << 11) | (g << 5) | b);
            line[x*2 + 0] = (uint8_t)(rgb565 & 0xFF);
            line[x*2 + 1] = (uint8_t)(rgb565 >> 8);
        }
        if (write(fbfd, line, (size_t)s->w * 2) < 0) break;
    }
    free(line);
}

// Escreve RGB888 direto (para bpp=24) ou RGBX (para bpp=32 — aqui só jogamos 3 bytes, ajuste se necessário)
static void write_to_fb_rgb24_like(int fbfd, const Surface *s, int bpp) {
    if (bpp == 24) {
        // Framebuffer pode esperar BGR; se a sua tela ficar com cores trocadas, inverta a ordem abaixo
        for (int y=0; y<s->h; ++y) {
            for (int x=0; x<s->w; ++x) {
                size_t si = ((size_t)y * s->w + x) * 3;
                uint8_t rgb[3] = { s->pix[si+0], s->pix[si+1], s->pix[si+2] };
                write(fbfd, rgb, 3);
            }
        }
    } else if (bpp == 32) {
        // Escreve como RGBX (X=0). Se precisar BGRA, ajuste a ordem.
        for (int y=0; y<s->h; ++y) {
            for (int x=0; x<s->w; ++x) {
                size_t si = ((size_t)y * s->w + x) * 3;
                uint8_t rgba[4] = { s->pix[si+0], s->pix[si+1], s->pix[si+2], 0 };
                write(fbfd, rgba, 4);
            }
        }
    }
}

int main(void) {
    char fbdev[64];
    int fb_index = -1;
    if (!find_fb_by_name(TARGET_FB_NAME, fbdev, sizeof(fbdev), &fb_index)) {
        fprintf(stderr, "%s não encontrado\n", TARGET_FB_NAME);
        return 1;
    }

    int width=0, height=0;
    if (!read_virtual_size(fb_index, &width, &height)) {
        fprintf(stderr, "Falha ao ler virtual_size de fb%d\n", fb_index);
        return 1;
    }

    char bpp_path[128];
    snprintf(bpp_path, sizeof(bpp_path), "/sys/class/graphics/fb%d/bits_per_pixel", fb_index);
    int bpp = read_int_file(bpp_path, 16);

    // Fonts
    Font fontBold, fontReg;
    if (!font_load(&fontBold, FONT_BOLD_TTF)) {
        fprintf(stderr, "Não consegui carregar fonte: %s\n", FONT_BOLD_TTF);
        return 1;
    }
    if (!font_load(&fontReg, FONT_REG_TTF)) {
        fprintf(stderr, "Não consegui carregar fonte: %s\n", FONT_REG_TTF);
        return 1;
    }

    // Imagem (opcional)
    int logo_w=0, logo_h=0; unsigned char *logo_rgba = NULL;
    struct stat st; if (stat(IMG_PATH, &st) == 0) {
        logo_rgba = load_image_rgba(IMG_PATH, &logo_w, &logo_h);
        if (!logo_rgba) fprintf(stderr, "Falha ao carregar imagem %s\n", IMG_PATH);
    }

    int fbfd = open(fbdev, O_WRONLY);
    if (fbfd < 0) {
        perror("open framebuffer");
        return 1;
    }

    for (;;) {
        Surface s = surface_make(width, height);
        // Fundo preto
        fill_rect(&s, 0, 0, width, height, 0, 0, 0);

        // Hora/Data
        char buf1[128], buf2[128];
        time_t now = time(NULL); struct tm tmv; localtime_r(&now, &tmv);
        strftime(buf1, sizeof(buf1), "Hora: %H:%M:%S", &tmv);
        strftime(buf2, sizeof(buf2), "Data: %d/%m/%Y", &tmv);

        // Título
        draw_text_string(&s, &fontBold, TITLE_TEXT, (float)FONT_BIG_PX, 10, 10, 255, 255, 0); // amarelo
        // Hora
        draw_text_string(&s, &fontBold, buf1, (float)FONT_BIG_PX, 10, 50, 255, 255, 0);
        // Data
        draw_text_string(&s, &fontReg, buf2, (float)FONT_SMALL_PX, 10, 90, 0, 255, 255); // ciano

        // Logo (canto inferior direito)
        if (logo_rgba) {
            int pos_x = width  - logo_w - 10;
            int pos_y = height - logo_h - 10;
            if (pos_x < 0) pos_x = 0; if (pos_y < 0) pos_y = 0;
            blit_rgba(&s, pos_x, pos_y, logo_rgba, logo_w, logo_h);
        }

        // Rotação
        Surface out = rotate_surface(&s, ROTATE_DEG);
        surface_free(&s);

        // Volta para o início do arquivo antes de escrever
        lseek(fbfd, 0, SEEK_SET);
        if (bpp == 16) {
            write_to_fb_rgb565(fbfd, &out);
        } else {
            write_to_fb_rgb24_like(fbfd, &out, bpp);
        }

        surface_free(&out);
        // Intervalo
        usleep(1000 * 1000); // 1s
    }

    // Cleanup (nunca chega aqui neste loop)
    if (logo_rgba) stbi_image_free(logo_rgba);
    font_free(&fontBold); font_free(&fontReg);
    close(fbfd);
    return 0;
}
