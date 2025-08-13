// fb_gif.c — Exibe GIF animado no framebuffer /dev/fbX (ILI9486)
// ----------------------------------------------------------------------
// Requisitos:
//   - giflib (leitura de GIF animado)
//       sudo apt-get update && sudo apt-get install -y libgif-dev giflib-tools
//   - (Opcional) Sem libs extras para resize — uso nearest-neighbor embutido.
//
// Compilação:
//   gcc -O2 -Wall -Wextra fb_gif.c -o fb_gif -lgif -lm
// Execução:
//   sudo ./fb_gif /home/dw/painel/kakashi.gif [rotacao 0/90/180/270]
//
// Recursos:
//   - Detecta automaticamente /dev/fbX pelo nome "fb_ili9486" (ajustável).
//   - Lê width/height via fbset (fallback 320x480), bpp e stride via sysfs.
//   - Carrega todos os frames do GIF e respeita a duração de cada um.
//   - Redimensiona proporcionalmente para caber na tela e centraliza no canvas preto.
//   - Respeita transparência (índice transparente do GCB).
//   - Converte para RGB565 (LE) quando bpp=16; suporta 24/32 bpp.
//   - Rotação 0/90/180/270.

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <stdint.h>
#include <stdbool.h>
#include <string.h>
#include <time.h>
#include <unistd.h>
#include <fcntl.h>
#include <glob.h>
#include <sys/stat.h>
#include <sys/types.h>

#include <gif_lib.h>

// ================= Configurações =====================
static const char *TARGET_FB_NAME = "fb_ili9486";  // /sys/class/graphics/fb*/name
static int ROTATE_DEG = 0;                          // 0, 90, 180, 270
// ====================================================

// ---------- Utilidades de arquivo/texto ----------
static bool read_text_file(const char *path, char *buf, size_t bufsz) {
    FILE *f = fopen(path, "r");
    if (!f) return false;
    size_t n = fread(buf, 1, bufsz - 1, f);
    fclose(f);
    if (n == 0) return false;
    buf[n] = '\0';
    return true;
}

static int read_int_file(const char *path, int defval) {
    char buf[128];
    if (!read_text_file(path, buf, sizeof(buf))) return defval;
    int v = defval; sscanf(buf, "%d", &v); return v;
}

// ---------- Descoberta de framebuffer ----------
static bool find_fb_by_name(const char *target, char *out_dev, size_t out_sz, int *out_index) {
    glob_t g = (glob_t){0};
    if (glob("/sys/class/graphics/fb*/name", 0, NULL, &g) != 0) return false;
    bool ok = false;
    for (size_t i=0; i<g.gl_pathc; ++i) {
        char namebuf[128];
        if (!read_text_file(g.gl_pathv[i], namebuf, sizeof(namebuf))) continue;
        // trim
        for (char *p = namebuf; *p; ++p) if (*p=='\n' || *p=='\r') *p='\0';
        if (strcmp(namebuf, target) == 0) {
            int idx = -1;
            if (sscanf(g.gl_pathv[i], "/sys/class/graphics/fb%d/name", &idx) == 1) {
                snprintf(out_dev, out_sz, "/dev/fb%d", idx);
                if (out_index) *out_index = idx;
                ok = true; break;
            }
        }
    }
    globfree(&g);
    return ok;
}

// Lê geometria: tenta fbset, senão fallback 320x480; lê bpp e stride
static void fb_geometry(const char *fbdev, int *w, int *h, int *bpp, int *stride) {
    int idx = 0; sscanf(fbdev, "/dev/fb%d", &idx);

    // width/height via fbset -s -fb /dev/fbX
    FILE *fp = NULL; char cmd[128]; char line[256];
    int tmpW = 0, tmpH = 0;
    snprintf(cmd, sizeof(cmd), "fbset -s -fb %s 2>/dev/null", fbdev);
    fp = popen(cmd, "r");
    if (fp) {
        while (fgets(line, sizeof(line), fp)) {
            int gw=0, gh=0; // linha: geometry <w> <h> ...
            if (sscanf(line, " geometry %d %d", &gw, &gh) == 2) { tmpW=gw; tmpH=gh; }
        }
        pclose(fp);
    }
    if (tmpW<=0 || tmpH<=0) { tmpW=320; tmpH=480; } // fallback usual da MPI3501

    char path[256];
    snprintf(path, sizeof(path), "/sys/class/graphics/fb%d/bits_per_pixel", idx);
    int tmpBpp = read_int_file(path, 16);

    int tmpStride = 0;
    snprintf(path, sizeof(path), "/sys/class/graphics/fb%d/stride", idx);
    tmpStride = read_int_file(path, 0);
    if (tmpStride <= 0) {
        snprintf(path, sizeof(path), "/sys/class/graphics/fb%d/fb_fix/line_length", idx);
        tmpStride = read_int_file(path, 0);
    }
    if (tmpStride <= 0) tmpStride = tmpW * (tmpBpp/8);

    *w = tmpW; *h = tmpH; *bpp = tmpBpp; *stride = tmpStride;
}

// ---------- Superfície RGB888 ----------
typedef struct { int w, h; uint8_t *pix; } Surface;

static Surface surface_make(int w, int h) {
    Surface s; s.w=w; s.h=h; s.pix=(uint8_t*)calloc((size_t)w*h*3,1); return s;
}
static void surface_free(Surface *s){ free(s->pix); s->pix=NULL; s->w=s->h=0; }
static inline void put_rgb(Surface *s,int x,int y,uint8_t R,uint8_t G,uint8_t B){
    if ((unsigned)x>=(unsigned)s->w || (unsigned)y>=(unsigned)s->h) return;
    size_t i=((size_t)y*s->w+x)*3; s->pix[i]=R; s->pix[i+1]=G; s->pix[i+2]=B;
}
static void fill_rect(Surface *s,int x,int y,int w,int h,uint8_t R,uint8_t G,uint8_t B){
    if (w<=0 || h<=0) return;
    int x0 = x < 0 ? 0 : x;
    int y0 = y < 0 ? 0 : y;
    int x1 = x + w; if (x1 > s->w) x1 = s->w;
    int y1 = y + h; if (y1 > s->h) y1 = s->h;
    for (int yy = y0; yy < y1; ++yy) {
        for (int xx = x0; xx < x1; ++xx) {
            put_rgb(s, xx, yy, R, G, B);
        }
    }
}
static inline void blend_rgba_over(Surface *s,int x,int y,uint8_t r,uint8_t g,uint8_t b,uint8_t a){
    if ((unsigned)x>=(unsigned)s->w || (unsigned)y>=(unsigned)s->h) return;
    float A=a/255.0f; size_t i=((size_t)y*s->w+x)*3;
    s->pix[i+0]=(uint8_t)(r*A + s->pix[i+0]*(1.0f-A));
    s->pix[i+1]=(uint8_t)(g*A + s->pix[i+1]*(1.0f-A));
    s->pix[i+2]=(uint8_t)(b*A + s->pix[i+2]*(1.0f-A));
}

// ---------- Rotação ----------
static Surface rotate_surface(const Surface *s, int deg){
    if (deg==0){ Surface o=surface_make(s->w,s->h); memcpy(o.pix,s->pix,(size_t)s->w*s->h*3); return o; }
    if (deg==90){ Surface o=surface_make(s->h,s->w);
        for(int y=0;y<s->h;++y)for(int x=0;x<s->w;++x){ size_t si=((size_t)y*s->w+x)*3; int nx=s->h-1-y, ny=x; size_t di=((size_t)ny*o.w+nx)*3; memcpy(&o.pix[di], &s->pix[si], 3); }
        return o; }
    if (deg==180){ Surface o=surface_make(s->w,s->h);
        for(int y=0;y<s->h;++y)for(int x=0;x<s->w;++x){ size_t si=((size_t)y*s->w+x)*3; int nx=s->w-1-x, ny=s->h-1-y; size_t di=((size_t)ny*o.w+nx)*3; memcpy(&o.pix[di], &s->pix[si], 3); }
        return o; }
    if (deg==270){ Surface o=surface_make(s->h,s->w);
        for(int y=0;y<s->h;++y)for(int x=0;x<s->w;++x){ size_t si=((size_t)y*s->w+x)*3; int nx=y, ny=s->w-1-x; size_t di=((size_t)ny*o.w+nx)*3; memcpy(&o.pix[di], &s->pix[si], 3); }
        return o; }
    Surface o=surface_make(s->w,s->h); memcpy(o.pix,s->pix,(size_t)s->w*s->h*3); return o;
}

// ---------- Resize nearest-neighbor para RGBA ----------
static unsigned char* resize_rgba_nn(const unsigned char *src,int sw,int sh,int dw,int dh){
    unsigned char *dst=(unsigned char*)malloc((size_t)dw*dh*4); if(!dst) return NULL;
    for(int y=0;y<dh;++y){ int sy = (int)((y*(double)sh)/dh); if(sy>=sh) sy=sh-1;
        for(int x=0;x<dw;++x){ int sx=(int)((x*(double)sw)/dw); if(sx>=sw) sx=sw-1;
            const unsigned char *sp = src + ((size_t)sy*sw+sx)*4;
            unsigned char *dp = dst + ((size_t)y*dw+x)*4;
            dp[0]=sp[0]; dp[1]=sp[1]; dp[2]=sp[2]; dp[3]=sp[3];
        }
    }
    return dst;
}

// ---------- Conversões para escrita no FB ----------
static void write_surface_to_fb_rgb565_le(int fbfd, const Surface *s, int stride){
    int row_bytes = s->w * 2; // 16bpp
    uint8_t *line = (uint8_t*)malloc((size_t)row_bytes);
    if (!line) return;
    lseek(fbfd, 0, SEEK_SET);
    for(int y=0;y<s->h;++y){
        for(int x=0;x<s->w;++x){ size_t si=((size_t)y*s->w+x)*3; uint8_t R=s->pix[si], G=s->pix[si+1], B=s->pix[si+2];
            uint16_t r=R>>3, g=G>>2, b=B>>3; uint16_t rgb565=(uint16_t)((r<<11)|(g<<5)|b);
            line[x*2+0]=(uint8_t)(rgb565 & 0xFF); line[x*2+1]=(uint8_t)(rgb565>>8);
        }
        write(fbfd, line, row_bytes);
        if (stride>row_bytes){ static const uint8_t z[4096]={0}; int pad=stride-row_bytes; while(pad>0){ int chunk= pad> (int)sizeof(z) ? (int)sizeof(z) : pad; write(fbfd, z, chunk); pad-=chunk; }
        }
    }
    free(line);
}

static void write_surface_to_fb_rgb24_32(int fbfd, const Surface *s, int bpp, int stride){
    lseek(fbfd, 0, SEEK_SET);
    int pxbytes = bpp/8; int row_bytes = s->w * pxbytes;
    for(int y=0;y<s->h;++y){
        for(int x=0;x<s->w;++x){ size_t si=((size_t)y*s->w+x)*3; uint8_t R=s->pix[si], G=s->pix[si+1], B=s->pix[si+2];
            if (bpp==24){ uint8_t rgb[3]={R,G,B}; write(fbfd, rgb, 3); }
            else { uint8_t rgba[4]={R,G,B,0}; write(fbfd, rgba, 4); }
        }
        if (stride>row_bytes){ static const uint8_t z[4096]={0}; int pad=stride-row_bytes; while(pad>0){ int chunk= pad> (int)sizeof(z) ? (int)sizeof(z) : pad; write(fbfd, z, chunk); pad-=chunk; }
        }
    }
}

// ---------- Estruturas para frames ----------
typedef struct { unsigned char *rgba; int w,h; double secs; } GifFrame; // rgba com alpha

typedef struct { GifFrame *arr; int count; } GifAnim;

static void free_gifanim(GifAnim *A){
    if (!A || !A->arr) return;
    for (int i = 0; i < A->count; ++i) free(A->arr[i].rgba);
    free(A->arr);
    A->arr = NULL;
    A->count = 0;
}

// Converte ColorMapObject + SavedImage em RGBA; trata transparência simples
static unsigned char* savedimage_to_rgba(const SavedImage *si, const ColorMapObject *globalCM,
                                         int *outW, int *outH,
                                         int transparentIndex, bool hasTrans){
    int w = si->ImageDesc.Width;
    int h = si->ImageDesc.Height;
    *outW = w; *outH = h;
    const ColorMapObject *cm = si->ImageDesc.ColorMap ? si->ImageDesc.ColorMap : globalCM;
    if (!cm || !cm->Colors) return NULL;

    unsigned char *rgba = (unsigned char*)malloc((size_t)w*h*4);
    if (!rgba) return NULL;

    const GifByteType *idx = (const GifByteType*)si->RasterBits;
    for (int y = 0; y < h; ++y) {
        for (int x = 0; x < w; ++x) {
            int k = idx[y*w + x];
            GifColorType c = cm->Colors[k];
            unsigned char *p = rgba + ((size_t)y*w + x)*4;
            p[0] = c.Red; p[1] = c.Green; p[2] = c.Blue;
            p[3] = (hasTrans && k == transparentIndex) ? 0 : 255;
        }
    }
    return rgba;
}

// Extrai duração (centésimos de segundo) do GCB de um frame SavedImage
static double frame_duration_secs(GifFileType *gif, int siIndex){
    // Padrão 0.10s quando ausente/zero
    double secs = 0.10;
#if GIFLIB_MAJOR >= 5
    GraphicsControlBlock gcb;
    if (DGifSavedExtensionToGCB(gif, siIndex, &gcb)==GIF_OK){
        int cs = gcb.DelayTime; if (cs <= 1) cs = 10; // normaliza para ~0.10s
        secs = cs / 100.0; if (secs <= 0.0) secs = 0.10;
    }
#endif
    return secs;
}

static bool load_gif_anim(const char *path, GifAnim *A){
    memset(A,0,sizeof(*A));
    int err=0; GifFileType *gif = DGifOpenFileName(path, &err); if (!gif){ fprintf(stderr, "DGifOpenFileName falhou (%d)\n", err); return false; }
    if (DGifSlurp(gif) != GIF_OK){ fprintf(stderr, "DGifSlurp falhou\n"); DGifCloseFile(gif,&err); return false; }

    int n = gif->ImageCount; if (n<=0){ DGifCloseFile(gif,&err); return false; }
    A->arr = (GifFrame*)calloc((size_t)n, sizeof(GifFrame)); if (!A->arr){ DGifCloseFile(gif,&err); return false; }
    A->count = n;
    for(int i=0;i<n;++i){
        SavedImage *si = &gif->SavedImages[i];
        int w,h;
        // Pega info de transparência e duração via GCB
        GraphicsControlBlock gcb; memset(&gcb, 0, sizeof(gcb));
#if GIFLIB_MAJOR >= 5
        DGifSavedExtensionToGCB(gif, i, &gcb);
#endif
        int  tIndex  = (gcb.TransparentColor != NO_TRANSPARENT_COLOR) ? gcb.TransparentColor : -1;
        bool tEnable = (gcb.TransparentColor != NO_TRANSPARENT_COLOR);

        // Converte para RGBA (com alpha usando tIndex)
        unsigned char *rgba = savedimage_to_rgba(si, gif->SColorMap, &w, &h, tIndex, tEnable);
        if (!rgba){ fprintf(stderr, "Falha RGBA frame %d\n", i); free_gifanim(A); DGifCloseFile(gif,&err); return false; }
        double secs = frame_duration_secs(gif, i);
        A->arr[i].rgba = rgba; A->arr[i].w = w; A->arr[i].h = h; A->arr[i].secs = secs;
    }
    DGifCloseFile(gif,&err);
    return true;
}

// Ajusta para caber em (W,H), mantendo proporção
static void fit_into(int srcW,int srcH,int maxW,int maxH,int *outW,int *outH){
    double sx = (double)maxW / (double)srcW;
    double sy = (double)maxH / (double)srcH;
    double s = sx < sy ? sx : sy; if (s>1.0) s=1.0; // não amplia
    int dw=(int)(srcW*s); int dh=(int)(srcH*s); if (dw<1) dw=1; if (dh<1) dh=1;
    *outW=dw; *outH=dh;
}

int main(int argc, char **argv){
    if (argc < 2){
        fprintf(stderr, "Uso: %s <caminho.gif> [rotacao(0/90/180/270)]\n", argv[0]);
        return 1;
    }
    const char *gif_path = argv[1];
    if (argc >= 3) ROTATE_DEG = atoi(argv[2]);

    // Descobre framebuffer
    char fbdev[64]; int fb_index=-1;
    if (!find_fb_by_name(TARGET_FB_NAME, fbdev, sizeof(fbdev), &fb_index)){
        fprintf(stderr, "Framebuffer '%s' não encontrado.\n", TARGET_FB_NAME);
        return 1;
    }

    int W=0,H=0,BPP=16,STRIDE=0; fb_geometry(fbdev, &W,&H,&BPP,&STRIDE);
    fprintf(stderr, "[fb] %s: %dx%d @%dbpp stride=%d\n", fbdev, W,H,BPP,STRIDE);

    struct stat st; if (stat(gif_path,&st)!=0){ perror("GIF"); return 1; }
    GifAnim anim; if (!load_gif_anim(gif_path, &anim)){ fprintf(stderr, "Não foi possível carregar GIF.\n"); return 1; }

    int fbfd = open(fbdev, O_WRONLY); if (fbfd<0){ perror("open fb"); free_gifanim(&anim); return 1; }

    for(;;){ // loop infinito
        for(int i=0;i<anim.count;++i){
            GifFrame *F = &anim.arr[i];
            int dw, dh; fit_into(F->w, F->h, W, H, &dw, &dh);
            unsigned char *scaled = (F->w==dw && F->h==dh) ? F->rgba : resize_rgba_nn(F->rgba, F->w, F->h, dw, dh);
            bool need_free = (scaled != F->rgba);

            // Desenha em canvas preto, centralizado
            Surface s = surface_make(W,H); fill_rect(&s,0,0,W,H,0,0,0);
            int offx = (W - dw)/2; if (offx<0) offx=0;
            int offy = (H - dh)/2; if (offy<0) offy=0;
            for(int y=0;y<dh;++y){ for(int x=0;x<dw;++x){ const unsigned char *p = scaled + ((size_t)y*dw+x)*4; unsigned char a=p[3]; if (a==0) continue; blend_rgba_over(&s, offx+x, offy+y, p[0],p[1],p[2], a); }}

            // Rotação
            Surface out = rotate_surface(&s, ROTATE_DEG); surface_free(&s);

            // Escreve no framebuffer
            if (BPP==16) write_surface_to_fb_rgb565_le(fbfd, &out, STRIDE);
            else write_surface_to_fb_rgb24_32(fbfd, &out, BPP, STRIDE);
            surface_free(&out);
            if (need_free) free(scaled);

            // Espera a duração do frame
            double secs = anim.arr[i].secs; if (secs<=0.0) secs=0.10;
            struct timespec ts; ts.tv_sec = (time_t)secs; ts.tv_nsec = (long)((secs - ts.tv_sec) * 1e9);
            nanosleep(&ts, NULL);
        }
    }

    // Nunca chega aqui
    close(fbfd); free_gifanim(&anim); return 0;
}
