%% demo_bilinear.m —— 预扭曲到底把什么钉回去了
% 纯基础 MATLAB，无工具箱（Butterworth 极点自己写）。
% 运行： >> demo_bilinear

T  = 1;                       % 归一化采样周期
Ap = 3;                       % 通带允许衰减 dB（这里只看 -3 dB 点）
n  = 4;                       % 阶数
Op = 0.45*pi;                 % 数字通带边缘（弧度）

% 预扭曲：数字 Ωp -> 模拟 ωp = (2/T)tan(Ωp/2)
wp = (2/T)*tan(Op/2);

Om = linspace(1e-4, pi-1e-4, 3000);

H_pre  = 1./sqrt(1 + ( (2/T)*tan(Om/2) / wp ).^(2*n));   % 预扭曲后的数字响应
H_naive= 1./sqrt(1 + ( (2/T)*tan(Om/2) / Op ).^(2*n));   % 忘预扭曲（把 Ωp 当模拟 ωc）

figure('Color','w','Position',[80 80 900 460]); hold on; box on;
plot(Om/pi, 20*log10(H_pre),   'LineWidth', 2.4, 'Color', [0.06 0.46 0.43]);
plot(Om/pi, 20*log10(H_naive), '--', 'LineWidth', 2, 'Color', [0.86 0.15 0.15]);
yline(-3, ':', 'Color', [0.6 0.6 0.6]);
xline(Op/pi, 'k:');
xlabel('\Omega / \pi'); ylabel('|H| / dB');
title(sprintf('\\Omega_p = %.2f\\pi, n = %d：实线=预扭曲，虚线=忘预扭曲', Op/pi, n));
legend('预扭曲', '忘预扭曲', 'Location', 'southwest');
ylim([-80 5]); xlim([0 1]); grid on;

aPre   = 20*log10(interp1(Om, H_pre,   Op));
aNaive = 20*log10(interp1(Om, H_naive, Op));
w3     = 2*atan(Op/2)/pi;      % 忘预扭曲后真正的 -3 dB 点
fprintf('预扭曲设计：Ωp 处 %.1f dB（正好 -3 dB）\n', aPre);
fprintf('忘预扭曲  ：Ωp 处 %.1f dB，-3 dB 点被挪到 %.3fπ\n', aNaive, w3);
fprintf('Ωp 越靠近 π，tan 扭得越狠，偏移越大。\n');
