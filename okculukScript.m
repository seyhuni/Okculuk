% to do list
% 1- filtered sinyalleri mat file olarak kaydet!
% 2- kayýtlarý klasördeki ad.mat olarak githuba at ve linki paylaþ
% 3- 2.5 - 6 olarak gidecek, QE baþlangýç zamaný referans alýnarak.
% 4- git hub at SE timings_horizantal, script ve mat filelar. Deadline: 28i.
% 
clear variables; close all; clc;
addpath(genpath('C:\Users\asus\Desktop\okculuk_dataset'));
[FileName,PathName] = uigetfile('*.acq','Select acq file');
AcqFile=load_acq(fullfile(PathName,FileName));   %# pass file path as string
Structname = fieldnames(AcqFile);
assignin('base', 'eogData', AcqFile.(Structname{2}));
fs=200;
figure(1)
plot(eogData)
title('Raw EOG Data')
eogData=eogData-mean(eogData); 
[c,l]=wavedec(eogData,8,'db6');
a8 = wrcoef('a',c,l,'db6',8);
eogData_corrected=eogData-a8; %Baseline correction
figure(2)
plot(eogData_corrected)
set(gcf, 'Position', get(0, ['ScreenSize']));
zoom on;
waitfor(gcf, 'CurrentCharacter', char(13))

zoom reset
zoom off

title(['Choose the extraction point for outliers: ' num2str(FileName),'. Right click to select end point.'])
pause(1)
button = 1;
while sum(button) <= 1
    [xx,yy,button] = ginput(1);
end
outlier=xx;
close(figure(2))
eogData_corrected=eogData_corrected(1:outlier);
figure(2)
plot(eogData_corrected)
title('corrected signal (also extracted outlier)')
% now after baseline correction, we will check the instafreq.
% time=linspace(0,length(eogData_corrected)/200,length(eogData_corrected));
load('C:\Users\asus\Desktop\okculuk_dataset\SE_timings_Horizontal.mat')
files = dir('C:\Users\asus\Desktop\okculuk_dataset');
dirFlags = [files.isdir];
subFolders = files(dirFlags); 
subFolderNames = {subFolders(3:end).name};

timingIndex=find(contains(subFolderNames,FileName(1:2)));
SE_Ti=SE_timings(timingIndex,:);
SE_TIs=SE_Ti{:,:};
SE_TIsFreq=SE_TIs./60;
figure(3)
instfreq(eogData_corrected,fs)
hold on
for i=1:length(SE_TIsFreq)
    plot([SE_TIsFreq(i) SE_TIsFreq(i)],[0, 40],'m');
end
title('instant frequency of the data')
s=findobj('type','legend');
delete(s)
hold off
% instfreq(eogData_corrected,time)

Band    = (2 / fs) * [0.5, 30];
[B, A]  = butter(6, Band, 'Bandpass');   
filteredEog = filtfilt(B, A, double(eogData_corrected));
figure(4)
plot(filteredEog)
SE_TIs=SE_TIs.*200;
hold on
for i=1:length(SE_TIs)
    plot([SE_TIs(i) SE_TIs(i)],[min(filteredEog), max(filteredEog)],'m');
end
title('Timings on the Filtered Data')
hold off
% N=length(filteredEog);         %number of points
% t=(0:N-1)/fs;   %time vector
% sgFilteredEog = sgolayfilt(filteredEog,3,201);
% figure(5)
% plot(sgFilteredEog)
% hold on
% for i=1:length(SE_TIs)
%     plot([SE_TIs(i) SE_TIs(i)],[min(sgFilteredEog), max(sgFilteredEog)],'m');
% end
% title('Timings on the Smoothed Data')
% 
% hold off
% 
% Smoothed istemiyoruz ! filtered üzerinden gidelim. 
% zeros oluþturup prediction matrisini oluþturalým.
% Kesilen yerden
% 
% medianFreq=medfreq(sgFilteredEog,fs);
% instaFreqs=instfreq(sgFilteredEog,fs);
% % length(sgFilteredEog)/length(instaFreqs)
% 
% instafreqLocs=((instaFreqs>(medianFreq-0.05))&(instaFreqs<(medianFreq+0.05)));
% instafreqLocs=find(instafreqLocs>0);
% 
% figure(6)
% plot(instaFreqs)
% hold on
% for i=1:length(instafreqLocs)
% plot(instafreqLocs,instaFreqs(instafreqLocs),'r+','MarkerFaceColor','r')
% end
% title(['Detection of the FREQs in between '  num2str(medianFreq-0.05)  ' and '  num2str(medianFreq+0.05)  ' Hz'])
% hold off