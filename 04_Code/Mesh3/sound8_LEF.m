clear all;  close all;    clc;

SongURL='https://www.youtube.com/watch?v=DF3XjEhJ40Y';
SongName='LoveStory';
SongVersion='1';
SongDir='D:\drive_E_backup\';

global  y Freq
global CurrentDirectory; [status ,CurrentDirectory]=system('cd');
global SongOriginName; [status ,SongOriginName]=system([SongDir,'yt-dlp.exe --restrict-filenames --get-filename -f bestaudio ',SongURL]);
% SongOriginName=['Halo 1.webm '];
global SongOriginPath; SongOriginPath=['"',CurrentDirectory(1:end-1),'\',SongOriginName(1:end-1),'"'];
% SongOriginPath=['"N:\mat\Project\Mesh\',SongOriginName(1:end-1),'"'];
global SongTag;        SongTag=[SongName,' ',num2str(SongVersion)];
global Song;           Song=[SongDir,SongTag,'.wav'];


system([SongDir,'yt-dlp.exe --restrict-filenames  -f bestaudio ',SongURL]);
system(['ffmpeg -y -i ',SongOriginPath ,...
    '  -map 0:a -preset  slow -crf 10   -c:a pcm_f64le  "',Song,'" '],'-echo')

% % [filename, pathname]=uigetfile('*.wav','Select the MATLAB code file');

[y0,Fs] =audioread(Song);   %   ../Layla_60sec.wav
y = normalize(y0,'range',[-0.5 0.5]);
% plot([0:(1/Fs):stop-(1/Fs)],y0(23:stop*Fs+22),'r',[0:(1/Fs2):stop-(1/Fs2)],y02(2323:(stop*Fs2+2322)),'b')
    
% song = audioplayer(y, Fs);   %data for the song rate     % whilecondition = song.Running;
time=0;
a=1;
N=500;
c(N,N)=0;
colormap hsv
m=500*4;
fs=44100;
dt = 1/fs;
t = (0:m-1)/fs;
n = pow2(nextpow2(m));

t2=0:0.01:24;
r2=t2;
y2=r2.*sin(t2);
x2=r2.*cos(t2);

t3=(pi):((2*pi)/12):((2*pi)*12.5);      %(pi):((2*pi)/12):((2*pi)*10);
length(t3);
Goldenratio=(1+sqrt(5))/2;
r3(25)=0;
r3(1)=2;
r3(11)=r3(1);
FirstRadiusDelta =(0.5+1.1)*(pi)/12;
R = FirstRadiusDelta;
FreqIndex=0;
Freq(500)=0;
RoundFreqIndex=0;
RoundFreq(100)=0;
FourierDisplay(500)=0;
xDisplay(381)=0;    yDisplay(381)=0;    cDisplay(381)=0;

clr = {'b','r'};    cstring='bmkrygcbmkrygc';
mycolormap=0;
length(t3);
RdStart=0.015;
RdEnd=-0.09;
(-(RdStart-RdEnd)/(length(t3)));
Rd=RdStart:(-(RdStart-RdEnd)/(length(t3))):(RdEnd);

for i=12:1:(length(t3)-2)

    r3(i)=r3(i-1)+R;

    R=((1+RdStart)+Rd(i))*R;
%     exp(-i/(length(t3)-12));
%     y3(i)=r3(i)*sin(t3(i));
%     x3(i)=r3(i)*cos(t3(i));
    

    deltat=(pi)/6;
    averager3=(r3(i)+r3(i-1))/2;
    jumplong=0.45;
    sector=0:jumplong:(averager3*deltat);
    lengthsector=length(sector)-1;
    if  ~exist('sectorgap', 'var'); sectorgap=0; end
%      disp(['(averager3*deltat):',num2str((averager3*deltat))])
        

    for i2=sectorgap:jumplong:lengthsector   
       FreqIndex=FreqIndex+1;
       CurrentRadius=(r3(i-1)+R*i2/lengthsector);
       CurrentAngle=(t3(i-1)+(deltat/lengthsector)*i2);
       Freq(FreqIndex)=(4*(2^( (-(3-1/3)*pi+CurrentAngle)/(2*pi) )));
%        CurrentRadius=hz2mel(Freq(FreqIndex))/28;
       Mark='kh';
       xDisplay(FreqIndex)= CurrentRadius*cos(CurrentAngle);
       yDisplay(FreqIndex)= CurrentRadius*sin(CurrentAngle);
       theta(FreqIndex)=CurrentAngle;
       Radius(FreqIndex)=CurrentAngle;
%       plot((averager3+R*i2/lengthsector)*cos(t3(i-1)+(deltat/lengthsector)*i2),(averager3+R*i2/lengthsector)*sin(t3(i-1)+(deltat/lengthsector)*i2),Mark,'MarkerSize',jumplong*5*10,'MarkerFaceColor',sectorcolor(i));
%          text(averager]3*cos(t3(i-1)+(deltat/lengthsector)*i2),averager3*sin(t3(i-1)+(deltat/lengthsector)*i2), [num2str(marker)]);
       hold on
    end
    sectorgap=jumplong-(lengthsector-i2);
      
     sectorcolor(i)=round((mod(i,12)));
      if ((mod(i,12))==11) % && sectorcolor(i-1)=='y');
          RoundFreqIndex=RoundFreqIndex+1; 
          RoundFreq(RoundFreqIndex)=Freq(FreqIndex);
%           disp(['mod(i,12):',num2str(mod(i,12))])
%           disp(['i:',num2str(i)])
%           disp(['sum(mycolormap):',num2str(sum(mycolormap))])
%           disp('---------------------------------------------------')
          mycolormap=[mycolormap(:);FreqIndex-sum(mycolormap-1)];
          
      end
      
    plot(xDisplay,yDisplay,'o'); drawnow;
%     plot(theta(1:end-1),diff(theta))
end


%     global  mtheta; mtheta=theta;
%     global  mRadius; mRadius=Radius;

    
    
%     [xDisplayIntegral,yDisplayIntegral]=draftTsul(Radius,FreqIndex);
% 
% plot(xDisplayIntegral,yDisplayIntegral,'-'); drawnow;




RoundFreqIndex=RoundFreqIndex+1; 
RoundFreq(RoundFreqIndex)=Freq(FreqIndex);
mycolormap=[mycolormap(:);round((FreqIndex-sum(mycolormap))*1.5)];

myjet(1,3)=0;
 for mycolormapindex=2:1:length(mycolormap)
%      clear ring ring1 ring2;
%      ring1=autumn(round(mycolormap(mycolormapindex)/2));
%      ring2=flip(autumn(round(mycolormap(mycolormapindex)/2) + (mod(mycolormap(mycolormapindex),2))));
%      ring=[ring1; ring2];
     
     ring=hsv(round(mycolormap(mycolormapindex)));
     myjet=[myjet;ring];
 end
    myjet=myjet(2:(FreqIndex+1),1:3);
    
    
    close Figure 1;

% % close all;  % % plot(x3,y3)

% % cd techila\lib\Matlab\      % % installsdk()        % % techilainit()


global cDisplay3AMP myFileFullName path cepstrum
% % % %*************** open a .mat file in Matlab ************************
% OpenFrameData


% close all;  record15_LEF(SongTag,Fs,y,FreqIndex,Freq,RoundFreqIndex,RoundFreq);   close all;

% % % %*************** save a .mat file in Matlab ************************
% SaveFrameData
% OpenFrameData
% load(['cDisplay_',SongTag,'.mat'], 'cDisplay3AMP');
% [cDisplay5iso226]=iso226sute11(Fs,y,cDisplay3AMP,FreqIndex,Freq,mycolormap,mycolormapindex); close all;
% h3 = piperecord11_LEF(SongTag,Fs,y0, cDisplay5iso226, "myFileFullName" ,...
%             xDisplay,yDisplay,myjet,Freq, theta, Radius);



    
load(['cDisplay_',SongTag,'.mat'], 'cDisplay3AMP');
 h3 = piperecord11_LEF(SongTag,Fs,y0, cDisplay3AMP, "myFileFullName" ,...
        xDisplay,yDisplay,myjet,Freq, theta, Radius);




system(['C:\ffmpeg\bin\ffmpeg -y -hide_banner -hwaccel nvdec -hwaccel_device 0 -vsync 0 ',...
        ' -i "N:\mat\Project\Mesh\',SongTag,'.mj2"  -i "',Song,'" ' ...
        '  -strict -2  -aspect 16:9 -filter:v scale=3840:2160  -c:v libx264 ',...
        '-c copy -c:v:0 hevc_nvenc -profile:v main10 -pix_fmt p016le -rc:v:0 vbr ',...
        '-rc-lookahead 32 -cq 1 -qmin 1 -qmax 51 -b:v:0 10M -maxrate:v:0 30M -gpu 1',...
        '  "N:\mat\Project\Mesh\N',SongTag,SongVersion,'4k.mov" '])    

    
% system(['C:\FFmpeg\bin\ffmpeg -i "N:\mat\Project\Mesh\',SongTag, ...
%         '.mj2"  -i "',Song,'"  -strict -2  -aspect 16:9 ',...
%         ' -filter:v scale=1280:720 -c:v libx264 -preset ',...
%         'slow -crf 10  -c:a copy   -shortest    "N:\mat\Project\Mesh\',...
%         SongTag,SongVersion,'s.mov"  -y'])
    
system(['C:\ffmpeg\bin\ffmpeg -i "N:\mat\Project\Mesh\',SongTag, ...
        '.mj2"  -i "',Song,'"  -strict -2  -aspect 16:9 ',...
        ' -filter:v scale=3840:2160 -c:v libx264 ',...
        '-preset slow -crf 10  -c:a copy   -shortest    "N:\mat\Project\Mesh\',...
        SongTag,SongVersion,'.mov"  -y'])


    
    
% system(['ffmpeg -y -i "',Song,'" -ss 0:0:30 -to 0:6:22 -i "D:\drive_E_backup\SeaCaveAmbience.mp4" ',...
%     '-filter_complex "[1]volume=-20dB[11];[0][11]amerge=inputs=2,pan=stereo|FL<c0+c1|FR<c2+c3[a]" -map "[a]" -preset  slow -crf 10  -c:a pcm_f32le output.wav'])
    

system(['ffmpeg -y -i ',SongOriginPath ,...
    '  -i "D:\drive_E_backup\',SongOriginName,'"   ',...
    '-filter_complex "[1]volume=-17dB[11];[0][11]amerge=inputs=2,pan=stereo|FL<c0+c2|FR<c1+c3[a]" ',...
    ' -map "[a]"  -c:a pcm_f64le  output.wav '])

system(['ffmpeg -y -i ',SongOriginPath ,...
    ' -ss 0:0:30 -to 0:6:22 -i "D:\drive_E_backup\',SongOriginName,'"   ',...
    '-filter_complex "[1]volume=-17dB[11];[0][11]amerge=inputs=2,pan=stereo|FL<c0+c2|FR<c1+c3[a]" ',...
    '  -map "[a]"   -c:a libopus   output.webm '])


% system(['ffmpeg -y -ss 30 -t 6:22 -i "D:\drive_E_backup\SeaCaveAmbience.mp4" ',...
%         ' -i "N:\mat\Project\Mesh\',SongTag,'.mj2"  -i output.wav  ',...
%         '  -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=3840x2160',...
%         '[bottom];   [1:v]setpts=PTS-STARTPTS, scale=3840:2160, format=yuv444p,fps=60,',...
%         'colorkey=0x000000:0.1:0.045[top];   [bottom][top]overlay=',...
%         'shortest=0, fps=60[v]"  -map [v] -map 2:a -c:v libx264 ',... 
%         '-c copy -c:v:0 hevc_nvenc  -profile:v main10 -pix_fmt p016le -rc:v:0 vbr_hq ',...
%         '-rc-lookahead 32 -cq 1 -qmin 1 -qmax 51 -b:v:0 10M -maxrate:v:0 30M -gpu 1',...
%         ' -aspect 16:9   out8.mov']) 
           %'-c:a copy -vcodec libx264',...

           
% system(['ffmpeg -y  -i "D:\drive_E_backup\GalaxyTraversal.mp4" ',...
%         ' -i "N:\mat\Project\Mesh\',SongTag,'.mj2"  -i output.wav  ',...
%         '  -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=3840x2160,fps=60',...
%         '[bottom];   [1:v]setpts=PTS-STARTPTS, scale=3840:2160, format=yuv444p,fps=60,',...
%         'colorkey=0x000000:0.1:0.045[top];   [bottom][top]overlay=',...
%         'shortest=0, fps=60[v]"  -map [v] -map 2:a -strict -2  -aspect 16:9   -c:v libx264  ',...
%         ' "N:\mat\Project\Mesh\out8.mov"']) 
           
   
system(['ffmpeg -y -ss 00:00:06 -i "D:\drive_E_backup\',SongOriginName,'"   ' ,...
'-i "N:\mat\Project\Mesh\',SongTag,'.mj2" -ss 00:00:00 -to 00:03:52 -i ',SongOriginPath ,...
'  -filter_complex "  [0:v]setpts=0.2*PTS, scale=3840x2160,fps=60',...
'[bottom];   [1:v]setpts=PTS-STARTPTS, scale=3840:2160, format=yuv444p,fps=60,',...
'colorkey=0x000000:0.03:0.0,boxblur=0:0:0:0:3:2[top];   [bottom][top]overlay',...
'[v]"  -map [v] -map 2:a -strict -2  -aspect 16:9   -c:v libx264  ',...
'-t 3:52 "N:\mat\Project\Mesh\out9.mov"'])
    


    
           
function OpenFrameData
    global cDisplay3AMP myFileFullName SongTag
    folder = 'N:\mat\Project\Mesh';  % You specify this!
    fullMatFileName = fullfile(folder,  ['cDisplay_',SongTag,'.mat']);
%     [cDisplay3AMP ]=load(fullMatFileName,'cDisplay3AMP' ).cDisplay3AMP;
    [cepstrum ]=load(fullMatFileName,'cepstrum' ).cepstrum;
%     [myFileFullName ]=load(fullMatFileName,'path' ).path;
end
function SaveFrameData
    global cDisplay3AMP path SongTag cepstrum
    folder = 'N:\mat\Project\Mesh';  % You specify this!
    fullMatFileName = fullfile(folder,  ['cDisplay_',SongTag,'.mat']);
    save(fullMatFileName,'cDisplay3AMP' , 'path' );
end
