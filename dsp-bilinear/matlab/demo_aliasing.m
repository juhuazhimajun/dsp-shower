%% demo_aliasing.m —— 听见「折返」：扫频 + 6 kHz 纯音
% 只用到基础 MATLAB（不依赖 Signal Processing Toolbox）
% 运行：  >> demo_aliasing
% 想听声音：把下面 PLAY 改成 true（需要音频设备）

PLAY = false;
fs   = 44100;
Td   = 6;
f0   = 200;  f1 = 7600;

t  = (0:1/fs:Td-1/fs).';
x  = sin(2*pi*(f0*t + (f1-f0)*t.^2/(2*Td)));          % 原声 44.1 kHz
fsl = 8000;
tl  = (0:1/fsl:Td-1/fsl).';
xl  = sin(2*pi*(f0*tl + (f1-f0)*tl.^2/(2*Td)));        % 按 8 kHz 直接取样（无抗混叠）

if PLAY
    sound(x, fs);  pause(Td + 0.3);
    sound(xl, fsl); pause(Td + 0.3);                   % 会听到 4 kHz 后音高「掉头」
end

%% 图 1：两个时频谱并排（手写 STFT，不需要 spectrogram 函数）
figure('Color','w','Position',[80 80 1200 420]);
subplot(1,2,1); showSpec(x, fs, 8000);
title('原声 44.1 kHz：一条笔直上行的斜线');
subplot(1,2,2); showSpec(xl, fsl, 8000);
title('8 kHz 采样：过 4 kHz 后折返下行');
xlabel('时间 / s');

%% 图 2：纯音骗局 6 kHz -> 2 kHz
figure('Color','w','Position',[80 80 800 320]);
tl2 = (0:1/fsl:0.9-1/fsl).';
x6l = sin(2*pi*6000*tl2);                              % 6 kHz 经 8 kHz 采样
subplot(1,2,1); showSpec(x6l, fsl, 4000);
title('6 kHz 过 8 kHz 采样：谱线落在 2 kHz');
t2 = (0:1/fs:0.9-1/fs).';
subplot(1,2,2); showSpec(sin(2*pi*2000*t2), fs, 4000);
title('真正的 2 kHz：完全一样');

fprintf('8000 - 6000 = 2000 Hz，所以采样后听起来就是 2 kHz。\n');
fprintf('扫频在 t=4 s 时理论频率 5.13 kHz，折叠后 %.0f Hz。\n', 8000 - 5133);

%% ---------- 局部函数 ----------
function showSpec(x, fs, fmax)
% 手写 STFT：帧长 1024，帧移 256，Hann 窗
    n = 1024; hop = 256;
    w = 0.5 - 0.5*cos(2*pi*(0:n-1).'/(n-1));   % Hann 窗，不依赖工具箱
    nf = floor((numel(x) - n)/hop) + 1;
    S = zeros(n/2+1, nf);
    for k = 1:nf
        seg = x((k-1)*hop + (1:n)) .* w;
        F = abs(fft(seg));
        S(:,k) = F(1:n/2+1);
    end
    S = 20*log10(S(1:n/2+1,:)/(sum(w)/2) + 1e-9);
    tt = ((0:nf-1)*hop + n/2)/fs;
    ff = (0:n/2).'*fs/n;
    imagesc(tt, ff, S, [-85 0]); axis xy;
    ylim([0 fmax]); colormap(magma2()); colorbar;
    ylabel('频率 / Hz'); xlabel('时间 / s');
end

function c = magma2()
% 简易 magma 近似（避免依赖额外 colormap）
    v = linspace(0,1,256).';
    c = [ (0.30*v.^0.6 + 0.12*v.^3), ...
          (0.02 + 0.55*v.^1.6), ...
          (0.25 + 0.62*sin(pi*v).^1.1) ];
    c = min(max(c,0),1);
end
