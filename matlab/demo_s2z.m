%% demo_s2z.m —— 把模拟左半平面搬到 z 平面：四种映射对比
% 纯基础 MATLAB，无工具箱。
% 运行： >> demo_s2z

T = 1;                                  % 归一化采样周期
[sg, om] = meshgrid(linspace(-3, 1, 25), linspace(-3.4, 3.4, 35));
S  = sg + 1j*om;
W  = linspace(-3.4, 3.4, 800);  Sw = 1j*W;   % jω 轴

maps = { ...
    '脉冲响应不变  z = e^{sT}',        @(s) exp(s*T); ...
    '前向差分  z = 1 + sT',            @(s) 1 + s*T; ...
    '后向差分  z = 1./(1 - s*T)',      @(s) 1./(1 - s*T); ...
    '双线性  z = (1+sT/2)./(1-sT/2)',  @(s) (1 + s*T/2)./(1 - s*T/2) };

figure('Color','w','Position',[60 60 1000 880]);
for k = 1:4
    subplot(2,2,k); hold on; box on;
    f = maps{k,2};
    Z = f(S);  Zb = f(Sw);
    valid = isfinite(Z);
    st = sg < 0;
    scatter(real(Z(st & valid)), imag(Z(st & valid)), 12, [0.18 0.62 0.42], 'filled', 'MarkerFaceAlpha', 0.55);
    scatter(real(Z(~st & valid)), imag(Z(~st & valid)), 12, [0.82 0.29 0.36], 'filled', 'MarkerFaceAlpha', 0.35);
    theta = linspace(0, 2*pi, 400);
    plot(cos(theta), sin(theta), 'k--', 'LineWidth', 1.1);
    plot(real(Zb), imag(Zb), 'LineWidth', 2, 'Color', [0.17 0.36 0.55]);
    z0 = f(-0.4 + 1.2j);
    plot(real(z0), imag(z0), 'p', 'MarkerSize', 14, 'MarkerFaceColor', 'k', 'MarkerEdgeColor', 'k');
    frac = mean(abs(Z(st & valid)) > 1);
    title(sprintf('%s   稳定点越界 %.0f%%', maps{k,1}, 100*frac), 'FontSize', 10);
    xlabel('Re'); ylabel('Im'); axis equal;
    lim = max(1.6, min(4, 1.2*max(abs([real(Zb) imag(Zb)]))));
    xlim([-lim lim]); ylim([-lim lim]);
    grid on;
end
sgtitle('把模拟左半平面搬到 z 平面：绿点 = 模拟稳定区，黑虚线 = 单位圆');
fprintf('前向差分：绿点有 %.0f%% 落到单位圆外 —— 模拟稳定、数字不稳定。\n', ...
        100*mean(abs(1 + S(sg < 0)*T) > 1));
fprintf('后向差分：稳定区全在 |z-1/2|<1/2 里，高频被挤在 z=1 附近。\n');
