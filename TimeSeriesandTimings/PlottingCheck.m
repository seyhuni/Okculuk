% Dosyaları (filtered signal ve timings) workspace'e load ettikten sonra run edip check etmek için bu script kullanılabilir. 

figure(1)
plot(filteredEog)
hold on
for i=1:length(SE_TIs_last)
    plot([SE_TIs_last(i) SE_TIs_last(i)],[min(filteredEog), max(filteredEog)],'m');
end
title('Timings on the Filtered Data')
hold off
