function  [h3]=piperecord11_LEF(SongTag,Fs,y,cDisplay9AMP,myFileFullName,xDisplay,yDisplay,myjet,Freq, theta, Radius)

    global  mtheta; mtheta=theta;
    global  mRadius; mRadius=Radius;
    
     [h3]=initializeTube(Fs,y,myjet,Freq,cDisplay9AMP);
     playloop(SongTag,y,cDisplay9AMP,Freq,h3,myFileFullName);

end


function [h3]=initializeTube(Fs,y,myjet,Freq,cDisplay9AMP)
    global ah R fig ts C mtheta mRadius u v fig

    global fs;  fs=Fs;    global dt; dt = 1/fs;
    global FrameNumberPerSecond;    FrameNumberPerSecond=60;
    global dFrame; dFrame=1/FrameNumberPerSecond;
    global m; m=dFrame/dt;
    global TotalSample; [TotalSample ,~]=size(y(:,1));  %Song.TotalSample; 
    global TotalFrameNumber; TotalFrameNumber=round(TotalSample/m);
    global FreqIndex; FreqIndex=length(Freq);


     set(0,'defaultfigurecolor',[0 0 0]);
    fig=figure('Position',[0 0 3840 2160]);    fig.MenuBar='none';    fig.Position=[0 0 3840 2160];     fig.WindowState='fullscreen'; % fig.WindowStyle='modal';
%     fig.MenuBar='figure';   fig.Position=[0 0 3840 2160]; 
    
    % create an axes that spans the whole gui
%      ah = axes('unit', 'normal', 'position', [0 0 1 1]);


%     SetSteadyBackGroundPhoto    
    set(gca,'handlevisibility','on', 'Visible','on');


    InerCircel=60;    R=linspace(-pi,pi,InerCircel);    [u,v]=meshgrid(mtheta,R);
    tsul=flip(u).*(0.01+0.0015*cDisplay9AMP(:,21)');
    x=(mRadius+(tsul).*cos(v)).*cos(u);    y=(mRadius+(tsul).*cos(v)).*sin(u);    z=(flip(mtheta))+(tsul).*(sin(v))-50;
    C=zeros(InerCircel,FreqIndex,3);
    for i=1:InerCircel;        C(i,:,:)=myjet(:,:);    end
    disp(['C:   ',num2str(length(myjet))]);
    
    set(gca,'NextPlot','add');    h3 = mesh(gca,x,y,z,C,'EdgeColor','interp', 'FaceColor','none','FaceLighting','gouraud');

    
    colormap(1-myjet);
    BL=155;    xlim([-300 300]);    ylim([-135 135]);    zlim([-75 45]);    view(270, 90);
    zlim([-200 BL]);
  %  camlight('headlight');     lighting phong;     
    h3.FaceAlpha='flat';     h3.AlphaData=h3.ZData;   %  disp(['h3.ZData:',num2str(max(h3.ZData))])
    set(gca, 'color', [0 0 0]);    set(gca,'xtick',[],'ytick',[],'ztick',[]);
    set(gca,'ZColor',[0 0 0]);    set(gca,'YColor',[0 0 0]);    set(gca,'XColor',[0 0 0]);%     v1 = get(h3,'FaceColor');   
     h3.AmbientStrength=0.3;    h3.EdgeAlpha=0.3;
%      h3.FaceColor = 'interp';
%     h3.FaceAlpha = 0.3;

    set(gca,'NextPlot','add');    
    ts = textscatter3(gca,[0 0 0],"  ");
    ts.FontName='Cambria';
    set(gca, 'Visible','on');


    function SetSteadyBackGroundPhoto
            % import the background image and show it on the axes
            bgp = imread('D:\drive_E_backup\background\casey.jpg');% image(bg);
            imagesc(bgp);
            %     bg = imresize(bg, [1280, 720]); image(bg);
            % prevent plotting over the background and turn the axis off
            set(ah,'handlevisibility','off','visible','off')
            % making sure the background is behind all the other uicontrols
            uistack(ah, 'bottom');
    end

    fig.WindowState='minimized';
end


function playloop(SongTag,y,cDisplay9AMP,Freq,h3,myFileFullName)
    global dFrame TotalFrameNumber  FrameNumberPerSecond ah  R  ts m C mtheta mRadius u v fig

    % Prepare the new file.
    videoFWriter = vision.VideoFileWriter(['N:\mat\Project\Mesh\',SongTag,'.mj2'],'FileFormat','MJ2000','FrameRate',FrameNumberPerSecond);   %,'AudioInputPort',true

%     [filter_mean_diff_cDisplay9AMP,mean_diff_cDisplay9AMP]=flowAMP(cDisplay9AMP);%     Temp_filter_mean_diff_cDisplay9AMP = round(normalize(filter_mean_diff_cDisplay9AMP,'range',[0 FreqIndex]));
%     filter_mean_diff_cDisplay9AMP = normalize(filter_mean_diff_cDisplay9AMP,'range',[0 1]);
    
%      [dd]=normalize(highpass(flowAMP(cDisplay9AMP),0.01),'range',[0 1]);%
%    [dd]=flowAMP2(cDisplay9AMP);
    
%     save('dd1.mat','dd')
%     load('dd2.mat', 'dd');
%     plot(x,highpass(filter_mean_diff_cDisplay9AMP,0.01),'r-');
%     [dim1 dim2] = size(cDisplay9AMP);
%       dd=diff(cDisplay9AMP,1,2);
%       dd=[dd';dd(:,1)']';
%       dd(:,30:(dim2-270))=normalize(dd(:,30:(dim2-270)),'range',[0 1]);


    global bg bgl_real bgw_real bg_l bg_w;  %     SetBackGroundPhoto;

    jf=java.text.DecimalFormat;
    % RadialWave initialize parameters (zz)
    u_min=min(u,[],'all');    u_max=max(u,[],'all');    u_range=(u_max-u_min)/2;
    V0=4.7124;    k=1;    omega=(2*(pi));    phaz=0; lmda=0;
    % CameraMotion initialize parameters
    daz=0.02;    az =270;
    del=0.02;    el = 13.90+del;        el_max=13.95;  el_min=9.95;
    nel = 13.90+del;
    PeriodicWave=@(t1) heaviside(mod(t1, 6*pi)-4*pi).*sin(mod(t1, 2*pi));
    iso226ForFreq(size(cDisplay9AMP,1))=0;
    for i=1:1:size(cDisplay9AMP,1); iso226ForFreq(i)=(iso226(40,Freq(i))/20); end
    maxIso226=1+max(iso226ForFreq,[],'all');
    % ObjectColor initialize parameter
    maxWhite=0;
    folder = 'N:\mat\Project\Mesh';
    % tracking initialize parameter
    global matObj PackIdx Packet FileName Packets matObjLen InitialSampleGap
    InitialSampleGap = 0; % load(fullfile(folder,'myFile001.mat')).cDisplay3PHAZ.OpenPack_sample;
    sample=0+InitialSampleGap;    t = 0;    RecordSemple=m*sample;  %60*m*12.5;% 60*m*60*2.5;
    matObjLen=30;
    FileName = (['myFile',sprintf('%02i',floor(sample./1000)),'1.mat']);
%     myFileFullName = fullfile(folder,FileName);
%     matObj = matfile(myFileFullName);
%     Packets=[]; matObjLen=length(matObj.cDisplay3PHAZ);
%     for i=1:matObjLen
%         Packet=(matObj.cDisplay3PHAZ(1,i));
%         if ~isempty(Packet.Precord); Packets=[Packets;Packet.Precord]; end
%     end
%     Packet = (matObj.cDisplay3PHAZ(1,(floor(sample./100)+1)));
    PackIdx = mod(sample-3,100);    if (PackIdx==0); PackIdx=100; end
    time=0;




    while ( sample<round((TotalFrameNumber)-26))  % == whilecondition);  % & sample<100
                                        tic;    RecordSemple=RecordSemple+m;    sample=round(RecordSemple/m);    t = t+dFrame;        sample_test=sample;

                                        
%                                         h3.XData=zeros(size(h3.XData));
%                                         h3.YData=zeros(size(h3.YData));
%                                         h3.ZData=zeros(size(h3.ZData));
%                                         h3.CData=zeros(size(h3.CData));
                                        
                                        
                                        [uV sV] = memory;
                                        disp(['sample:',num2str(sample-1),'     time:',num2str(time),'     sV.PhysicalMemory.Available:',char(jf.format(sV.PhysicalMemory.Available))]);
                                         %SetRadialWave;
                                        SetObjectColor;
%                                         UpdatePointer(sample)
%                                         disp(['sample:',num2str(sample),'     PackIdx: ',num2str(PackIdx),'     Packet:',num2str(Packet.Precord),'     FileName:',FileName]);
%                                         A3=(find(Packet.data(PackIdx,:,:)==max(Packet.data(PackIdx,:,:),[],2)));
%                                         A4=circshift( Packet.data(PackIdx,1:size(cDisplay9AMP,1),:) , -1*A3);
%                                         tsul=8*flip(u).*(((0.0003*cDisplay9AMP(:,sample)'))+...
%                                                         (0.00288.*fillmissing(real(squeeze(A4)).^1,'constant',0)'));  %
%                                         tsul=(maxIso226-iso226ForFreq(:))'.*flip(u).*(((0.0003*cDisplay9AMP(:,sample)'))+0.0003+...
%                                                         (0.00288.*fillmissing(real(squeeze(A4)),'constant',0)'));
%                                         tsul=(maxIso226-iso226ForFreq(:))'.*flip(u).*(((0.0002*cDisplay9AMP(:,sample)'))+0.0002+...
%                                                         (0.0019.*fillmissing(real(squeeze(A4)),'constant',0)'));
                                        tsul=(maxIso226-iso226ForFreq(:))'.*flip(u).*(((0.00003*cDisplay9AMP(:,sample)'))+0.00002);
%                                         tsul=flip(u).*(((0.0008*cDisplay9AMP(:,sample)'))+0.0002);

%                                         W=phaz+(u-u_min).*(lmda/u_range);
%                                         PeriodicWave=sin(W);   PeriodicWave(PeriodicWave<0)=0;

%                                         draft=ones(size(mean(tsul)))*mean(tsul,'all')*4;
%                                         [Draft]=draftTsul(mean(tsul));
%                                         tsul=tsul+draftTsul(mean(tsul));
                                         xy=(mRadius+-1*(tsul).*(cos(v)));   %+mean(tsul)*2;   %draft;  %                          <--(2) 
%                                         r=(1-1/pi)/(3);
%                                           xy=(mRadius+((tsul*((1-1/pi)/2))'.^(1-dd(:,sample)))'.*(cos(v)));
%                                           xy=-(mRadius+((tsul*(r/2))'.^(1-dd(:,sample)))'.*(cos(v)));
%                                           xy=(mRadius+(tsul).*-((r/3).^(1-dd(:,sample))').*(cos(v)));
%                                (1)-->     xy=(mRadius+(tsul).*(((r.*cos(v./pi))'.^(dd(:,sample)))').*(cos(v)));
                                      %     xy=(mRadius+(tsul)*(-((1-1/pi)/2).^(1-dd(sample))).*(cos(v)));
                                        %-(r/2).^(1-dd).*cos(v);
                                        
%                                         yy=(mtheta+(tsul).*(cos(v)));   %+mean(tsul)*2;   %draft;     %   
%                                         zz=(tsul).*sin(v)-50+(10*cos((pi/180)*el));
                                         zz=(tsul).*(0.79.*cos(v./4).*sin(v))-50+(10*cos((pi/180)*el)); %                          <--(2)  
%                                         zz=(tsul.*(((r.*cos(v./pi))'.^(dd(:,sample)))').*sin(v))-50+(10*cos((pi/180)*el));
%                          (1)-->         zz=(tsul.*-((r/3).^(1-dd(:,sample))').*sin(v))-50+(10*cos((pi/180)*el));
                                       % zz=(tsul.*(((1-1/pi).*cos(v./pi)).^(dd(sample)).*sin(v)))-50+(10*cos((pi/180)*el));
                                       % (r.*cos(v./pi)).^(dd).*sin(v)
                                        
%                                         zz=(2.*PeriodicWave(phaz+(u-u_min).*(lmda/u_range)))+(tsul).*sin(v)-40+(10*cos((pi/180)*el));    %+mean(tsul)*2;     %+Draft*(1.6180339887498948482)
                                        cc=C-flip(u).*(0.01)+flip(u).*(0.0035*cDisplay9AMP(:,sample)')./maxWhite;

                                        clear h3.XData h3.YData h3.ZData h3.CData;
                                        h3.XData=xy.*cos(u+pi-((2*pi/(60*180))*sample));    %
%                                         h3.YData=yy.*(sin(u+pi/2)/2);
                                        h3.YData=xy.*sin(u+pi-((2*pi/(60*180))*sample));    %+yDraft
                                        
                                        h3.ZData=zz;
                                        h3.CData=cc;
                                        
                                        

                                        %[tsulMax,tsulMaxIdx] = max(tsul,[],'all','linear');
                                        %[tsulMaxIdx tsulMaxIdy]=find(tsul==tsulMax);
                                        textSide=45;%mod(sample,60)+1;
                                        tsXYZ=[h3.XData(textSide,:); h3.YData(textSide,:); h3.ZData(textSide,:)];
                                        tsColor=h3.CData(textSide,:,:);
                                        tsColor = min(tsColor,0);
                                        tsColor = max(tsColor,1);
                                        SetTextData(tsXYZ,tsColor,textSide)  %normalize(tsColor,'range',[0 1])
                                        SetCameraMotion
%                                         rotate3d on;

                                        F=getframe(gcf);%1280 720%,[0 0 3840 2160]
                                        step(videoFWriter,(F.cdata)); %, y((m*(sample-1)+1):(m*sample)+0,:)); 
                                        time = toc;
%                                         disp(['time:',num2str(time),'     sample:',num2str(sample),'     az:',num2str(az),'     el:',num2str(el),'     del:',num2str(del),'     ts.ZData:',num2str(ts.ZData) ]);    %,'     tsul:',num2str(max(flip(u).*(0.0015*cDisplay9AMP(:,sample)'),[],'all'))
                                        
    end

    delete(h3);    release(videoFWriter);    close all;

    
    function [DisplayIntegral]=draftTsul(Radius)
    FreqIndex=length(Radius);
    %Goldenratio=(1+sqrt(5))/2;
    expdiv2=exp(1)/2;
    DisplayIntegral(FreqIndex)=0;
        for i_draft=1:FreqIndex
               DisplayIntegral(i_draft)=(Radius(i_draft)*(1))+mean(DisplayIntegral(MeanBack360(i_draft)),'omitnan')/(exp(1));
               %(1.6180339887498948482)+2*(i_draft/FreqIndex)^2)
        end
   
    function [nextRoll]=forward360(index)
        nextRoll = closestIndex(mtheta(index)+(2*pi),mtheta);
    end  
    function [rangePrevRoll]=MeanBack360(index)
        Scattering=9+round(6*( (mRadius(index)-mRadius(1))/(mRadius(FreqIndex)-mRadius(1)) ));
        rangePrevRoll = [max(1,Back360(index)-Scattering):1:(Back360(index)+Scattering)];
        %prevRoll = closestIndex(mtheta(index)-(2*pi),mtheta);
    end  
    function [prevRoll]=Back360(index)
        prevRoll = closestIndex(mtheta(index)-(2*pi),mtheta);
    end    
    function [closestValue]=closestValue(A,V)
        [minValue,closestIndex] = min(abs(A-V'));
        closestValue = N(closestIndex);
    end
    function [closestIndex]=closestIndex(A,V)
        [minValue,closestIndex] = min(abs(A-V'));
    end
 end
    function SetBackGroundPhoto
        global isBackGroundPhoto; isBackGroundPhoto=true;
        bg = imread('/media/niv/New Volume/drive_E_backup/background/casey.jpg');
        [bgl_real ,bgw_real ,~] = size(bg);
        if (bgw_real >= bgl_real);   bg_l=bgl_real;  bg_w=round((bg_l/720)*1280);  end
        if (bgl_real >= bgw_real);  bg_w=bgw_real;    bg_l=round((bg_w/1280)*720);    end
    end
    function SetObjectColor
        maxWhite=max(flip(u).*(0.0035*cDisplay9AMP(:,sample)'),[],'all'); %sample_test
    end
    function SetRadialWave
        
        T=(100)*dFrame;%*dFrame);
        dT=0.5*cos(((2*pi)/(60*10))*sample)*dFrame;
        fdT=(1/dT);
        fT=(1/T);
        f=fT;%+0.2*cos(((2*pi)/(60*10))*mod(sample,60*10));

%         T =60*dFrame; % 1[sec]
%         lmda=1.5*(pi); %

        old_omega=omega;
        omega=(2*(pi)*f);

        old_k=k;
        k=omega/V0;%(2*pi)/lmda;
%         V0=omega/k;
        lmda=4.8701;%(2*pi)/k;
        V=lmda/f;
        Vg=(omega-old_omega)/(k-old_k);
        speed=700*dFrame;
        Xt=speed; %*filter_mean_diff_cDisplay9AMP(sample); %cos(((2*pi)/(60*10))*mod(sample,60*10));
        phaz=omega*(t*4)*(-1);
        
        %  disp(['     phaz:',num2str(phaz),'     Xt:',num2str(Xt)]);
       %   disp(['     t:',num2str(t),'     sample:',num2str(sample),'     AMP:',num2str(2),'  T/dFr',num2str(T/dFrame),'    omega:',num2str(omega),'    k:',num2str(k),'    f:',num2str(f),'  Vg:',num2str(Vg),'  V0:',num2str(V0),'  V:',num2str(V),'   lmda:',num2str(lmda)]);
    end     
    function SetTextData(tsXYZ,tsColor,textSide)

        
%         ts.XData=cDisplay(1,1800);    ts.YData=cDisplay(2,1800);    ts.ZData=cDisplay(3,1800);
        %ts.TextData=string(['M',num2str(textSide)]);  %sample:',num2str(sample),'     FileName:',FileName]);       %string(Xt);filter_mean_diff_cDisplay9AMP(sample)
        %Temp=2; %round(filter_mean_diff_cDisplay9AMP(sample));
        %ts.ColorData= [C(1,Temp,1) C(1,Temp,2) C(1,Temp,3)];
        
        
        persistent LabelsState;
        persistent Solfege;
        if isempty(Solfege)
            Solfege(1).Name='Do';
            Solfege(1).Octave_name=["Subsubcontra",	"Subcontra",	"Contra",	"Great",	"Small",	"One-lined",	"Two-lined",	"Three-lined",	"Four-lined",	"Five-lined",	"Six-lined",	"Seven-lined"];
            Solfege(1).Scientific_designation=...
                              ["C?2",       "C?1",      "C0",     "C1",       "C2",       "C3",        "C4",       "C5",         "C6",         "C7",          "C8",      "C9",	"C10"];
            Solfege(1).Freqs =[4.088,      8.176,      16.352,     32.703,     65.406,     130.813,     261.626,     523.251,     1046.502,     2093.005,      4186.009];    %,
            Solfege(1).label(length(Solfege(1).Freqs)+1).ts=0;
            
            Solfege(2).Name='Re';
            Solfege(2).Scientific_designation=...
                              ["D?2",       "D?1",      "D0",     "D1",       "D2",       "D3",        "D4",       "D5",         "D6",         "D7",          "D8",      "D9",	"D10"];
            Solfege(2).Freqs =[4.5885,     9.177,      18.354,     36.708,     73.416,     146.832,     293.665,     587.33,      1174.659,     2349.318,      4698.636];    %,     9397.273,      18794.545];
            Solfege(2).label(length(Solfege(2).Freqs)+1).ts=0;
            
            Solfege(3).Name='Mi';
            Solfege(3).Scientific_designation=...
                              ["E?2",       "E?1",      "E0",     "E1",       "E2",       "E3",        "E4",       "E5",         "E6",         "E7",          "E8",      "E9",	"E10"];
            Solfege(3).Freqs =[5.150,      10.301,     20.602,     41.203,     82.407,     164.814,     329.628,     659.255,     1318.51,      2637.02,      5274.041];    %,     10548.082,     21096.164];
            Solfege(3).label(length(Solfege(3).Freqs)+1).ts=0;
            
            Solfege(4).Name='Fa';
            Solfege(4).Scientific_designation=...
                              ["F?2",       "F?1",      "F0",     "F1",       "F2",       "F3",        "F4",       "F5",         "F6",         "F7",          "F8",      "F9",	"F10"];
            Solfege(4).Freqs =[5.456,      10.913,     21.827,     43.654,     87.307,     174.614,     349.228,     698.456,     1396.913,     2793.826,     5587.652];    %,     11175.303,     22350.607];
            Solfege(4).label(length(Solfege(4).Freqs)+1).ts=0;
            
            Solfege(5).Name='Sol';
            Solfege(5).Scientific_designation=...
                              ["G?2",       "G?1",      "G0",     "G1",       "G2",       "G3",        "G4",       "G5",         "G6",         "G7",          "G8",      "G9",	"G10"];
            Solfege(5).Freqs=[6.125,      12.25,      24.5,       48.999,     97.999,     195.998,     391.995,     783.991,     1567.982	   3135.963,     6271.927];     %,     12543.854,     25087.708];
            Solfege(5).label(length(Solfege(5).Freqs)+1).ts=0;
            
            Solfege(6).Name='La';
            Solfege(6).Scientific_designation=...
                              ["A?2",     "A?1",     "A0",       "A1",       "A2",       "A3",        "A4",       "A5",         "A6",         "A7",         "A8",      "A9",	"A10"];
            Solfege(6).Freqs =[6.875,     13.75,      27.5,       55,         110,        220,         440,         880,         1760,         3520,         7040];         %,         14080,         28160];
            Solfege(6).label(length(Solfege(6).Freqs)+1).ts=0;
            
            Solfege(7).Name='Si';
            Solfege(7).Scientific_designation=...
                              ["B?2",      "B?1",     "B0",       "B1",       "B2",       "B3",        "B4",        "B5",         "B6",        "B7",         "B8",      "B9",	"B10"];
            Solfege(7).Freqs =[7.717,      15.434,     30.868,     61.735,     123.471,    246.942,     493.883,     987.767,     1975.533,     3951.066,     7902.133];    %,     15804.266,     31608.531];
            Solfege(7).label(length(Solfege(7).Freqs)+1).ts=0;
            
            LabelsState=LableText.Freqs;
        end       
        
        TransparencyOscillation=(1+sin(sample*(2*pi/(60*10))));
        if (TransparencyOscillation==0);     LabelsState=LabelsState.next;   end
        
        for note=1:7
            for octave=1:length(Solfege(note).Freqs)
                [minValue(octave),closestIndex(octave)] = min(abs(Solfege(note).Freqs(octave)-Freq'),[],1);
                cDisplayX(octave)=tsXYZ(1,closestIndex(octave));    cDisplayY(octave)=tsXYZ(2,closestIndex(octave));    cDisplayZ(octave)=tsXYZ(3,closestIndex(octave));
                cDisplayC(octave,:)=tsColor(1,closestIndex(octave),:);
                if isempty(Solfege(note).label(octave).ts)
                    set(gca,'NextPlot','add');
                    Solfege(note).label(octave).ts=textscatter3(gca,[cDisplayX(octave) cDisplayY(octave) cDisplayZ(octave)],string([num2str(Solfege(note).Freqs(octave)),'Hz']));
                    Solfege(note).label(octave).ts.TextData=string([num2str(Solfege(note).Freqs(octave),4),'Hz']);
                    Solfege(note).label(octave).ts.ColorData=abs(cDisplayC(octave,:));
                    Solfege(note).label(octave).ts.FontName='Cambria';
                    Solfege(note).label(octave).ts.FontSize=7+octave*0.12;
                    Solfege(note).label(octave).ts.FontWeight='bold';
                    Solfege(note).label(octave).ts.FontAngle='italic';
                    %tsDo(i).struct('ts',textscatter3(gca,[0 0 0]," "));
                else
                    Solfege(note).label(octave).ts.XData=cDisplayX(octave);
                    Solfege(note).label(octave).ts.YData=cDisplayY(octave);
                    Solfege(note).label(octave).ts.ZData=cDisplayZ(octave);
                    Solfege(note).label(octave).ts.ColorData=min([TransparencyOscillation*3, 1])*abs(cDisplayC(octave,:));
                    if (TransparencyOscillation==0)
                        switch LabelsState
                            case 'Freqs' 
                                Solfege(note).label(octave).ts.TextData=string([num2str(Solfege(note).Freqs(octave),4),'Hz']);
                            case 'Scientific_designation' 
                                Solfege(note).label(octave).ts.TextData=string(Solfege(note).Scientific_designation(octave));
                            case 'Name' 
                                Solfege(note).label(octave).ts.TextData=string(Solfege(note).Name);
                            case 'Octave_name'
                                Solfege(note).label(octave).ts.TextData=string(Solfege(1).Octave_name(octave));
                            otherwise
                                warning('Unexpected LabelsState type.')
                        end 
                    end
                    %if (sample>(5*60));    Solfege(note).label(octave).ts.TextData=string([" "]);    end
                end
            end
        end
        

% classdef LableText
%    enumeration
%       Freqs, Scientific_designation, Name, Octave_name
%    end
%    methods
%       function tf = isMeetingDay(obj)
%          tf = LableText. obj.;
%       end
%    end
% end
% 
% 
% 
%         
% switch plottype
%     case 'Freqs' 
%         Solfege(note).label(octave).ts.TextData=string([num2str(Solfege(note).Freqs(octave),4),'Hz']);
%     case 'Scientific_designation' 
%         Solfege(note).label(octave).ts.TextData=string(Solfege(note).Scientific_designation(octave));
%     case 'Name' 
%         Solfege(note).label(octave).ts.TextData=string(Solfege(note).Name);
%     case 'Octave_name'
%         Solfege(note).label(octave).ts.TextData=string(Solfege(1).Octave_name(octave));
%     otherwise
%         warning('Unexpected plot type. No plot created.')
% end



%         set(gca,'NextPlot','add'); 
%         ts2=textscatter3(gca,[cDisplayX(1) cDisplayY(1) cDisplayZ(1)],string([num2str(Do(iDo)),'Hz']));
%         ts2.ColorData= [C(1,Temp,1) C(1,Temp,2) C(1,Temp,3)];
       % set(gca, 'Visible','off');
        
%             tsDo(iDo).TextData=string([num2str(Do(iDo)),'Hz']);
%             tsDo(iDo).ColorData= [C(1,Temp,1) C(1,Temp,2) C(1,Temp,3)];
            %tsDo(iDo)=textscatter3(gca,[cDisplay(1,closestIndex(iDo)) cDisplay(2,closestIndex(iDo)) cDisplay(3,closestIndex(iDo))],[num2str(round(Do(iDo)))]);

    end
    function SetCameraMotion 

%             if (el >= el_max-(30*sample/(TotalFrameNumber-4)))
%                 del=abs(del)*(-1);
%             end
%             if (el <=el_min)
%                 del=abs(del)*(1);
%             end
%             if (sample <= (TotalFrameNumber-4)*(1/4))  % (TotalFrameNumber-4)/2);
% %                 el = el+del*cos(pi*el/180);
% %                  sel=10+10*sin(sample/(60*30))+el;
%                  az = az+daz;
%             elseif (sample >= (TotalFrameNumber-4)*(3/4))
%                   az = az+daz;
% %                 el=el_max-0.90+del;
% %                 el = el+del*cos(pi*el/180);
%             else
%                  az = az+daz;
%             end
%             %         el = el+del;%*cos(pi*el/180)

%          if (az >= 300);
%             daz=daz*(-1);
%         end
%         if (az <= 240);
%             daz=daz*(-1);
%         end

%         el=90;            %19.95;
        nel = 25+5*sin((2*pi/(60*180))*sample)+el;
        az = 270 + mod((360/(60*180))*sample,360);
        view(az, nel);
%         camlight(az,nel)
%         view( 180*sin(el), 90*abs(el));
%         zoom('off');
         teta_0to1=((el-(el_min+del))/(el_max-el_min));
%         teta_0to1=0;

         
        global isBackGroundPhoto
        if (isBackGroundPhoto==true)
                bg_x=0;
                bgy_horizon=floor(bgl_real/3);
                bgy_scale=(bgl_real-bgy_horizon)-bg_l;
                
                bg_y=bgy_horizon+round(teta_0to1*bgy_scale);   %round(bgw_real/2)+sample*3;
                imagesc(ah,bg( (1+bg_y):min(bg_l+bg_y,bgl_real),(1+bg_x):(bg_w+bg_x),: ));
        end
        
        set(gca,'CameraTarget',[0 0 -5-30]);
%         set(gca,'CameraTarget',[0 0 -5-30*teta_0to1]);
        ts.ZData=-5-30*teta_0to1;

       
        set(gca,'CameraViewAngleMode','manual');
        ctarg = get(gca,'CameraTarget');
        cpos = get(gca,'CameraPosition');
%        newcp = cpos - (0.979)*(cpos - ctarg);
%        newcp = cpos - (0.66-0.20*sin((pi/180)*el))*(cpos - ctarg);
        
         newcp = cpos - (0.80-0.20*sin((pi/180)*el))*(cpos - ctarg);
         
        set(gca,'CameraPosition',newcp);
%         set(gca,'CameraViewAngle',65);
%           set(gca,'CameraTarget',[20 0 0])

    end
    
    function UpdatePointer(sample)  
        if ~CheckInPack(sample)
            if ~CheckPacket(sample)
                if ~CheckFile(sample)
                    disp(['Error function UpdatePointer unable to find data for ',mat2str(sample)]);
                end
            end
        end
%         FileName = (['myFile',mat2str(floor(sample./1000)),'1.mat']);
%         Packet = floor((mod(sample,1000)./100));
%         PackIdx = mod(sample,100);
        
        function [isInPack]=CheckInPack(sample)
            firstPackIdx=Packet.OpenPack_sample;
            lastPackIdx=Packet.sample;
            isInPack=(firstPackIdx<=sample & sample<=lastPackIdx);
            if isInPack
                PackIdx = mod(sample-InitialSampleGap,100);
                if (PackIdx==0); PackIdx=100; end
            end
            return
        end
        function [isPack]=CheckPacket(sample)
            if ((Packet.Precord+1)<=matObjLen)
                newPacket = (matObj.cDisplay3PHAZ(1,Packet.Precord+1));
                if (newPacket.OpenPack_sample==sample)
                    Packet=newPacket;
                    clear newPacket;
                    isPack=CheckInPack(sample);
                    if (isPack);    return;     end
                end
                clear newPacket;
            end
            [firstPacket,lastPacket]=bounds(Packets);
            firstPacket=(matObj.cDisplay3PHAZ(1,firstPacket));
            lastPacket=(matObj.cDisplay3PHAZ(1,lastPacket));
            isPack=(firstPacket.OpenPack_sample<=sample & sample<=lastPacket.sample);
            clear firstPacket;      clear lastPacket;
            [firstPacket,lastPacket]=bounds(Packets);
            if isPack
                for iP=(firstPacket):1:(lastPacket)
                    clear Packet;
                    Packet = (matObj.cDisplay3PHAZ(1,iP));  %cDisplay3PHAZ(i).Precord;
                    isPack=CheckInPack(sample);
                    if (isPack)
                        pause(5);
                        return
                    end
                end
            end
            return

        end
        function [isFile]=CheckFile(sample)
            isFile=(0<exist(fullfile('N:\mat\Project\Mesh',...
                   ['myFile',sprintf('%02i',floor(sample./1000)),'1.mat']), 'file'));
            if isFile
                if ~strcmp(FileName,(['myFile',sprintf('%01i',floor(sample./1000)),'1.mat']))
                    FileName=(['myFile',sprintf('%02i',floor(sample./1000)),'1.mat']);
                    myFileFullName = fullfile('N:\mat\Project\Mesh',FileName);
%                     clear cDisplay3PHAZ;
                    disp(['Load New File: ',FileName]);
                    clear matObj;
                    matObj=matfile(myFileFullName);
                    clear Packets;
                    Packets=[];
                    matObjLen=length(matObj.cDisplay3PHAZ);
                    for iPs=1:matObjLen
                        clear Packet;
                        Packet=(matObj.cDisplay3PHAZ(1,iPs));
                        if ~isempty(Packet.Precord); Packets=[Packets;Packet.Precord]; end
                    end
                    isFile = CheckPacket(sample);
                    if (isFile)
                        return
                    end
                end
            end
            return
        end
    end
       
      
end



function [filter_mean_diff_cDisplay9AMP,mean_diff_cDisplay9AMP ]=flowAMP(cDisplay9AMP)  %filter_mean_diff_cDisplay9AMP
%     filter_mean_diff_cDisplay9AMP
    n=length(cDisplay9AMP);
%     diff_cDisplay9AMP = diff(abs(cDisplay9AMP).^2/n);
    diff_cDisplay9AMP = abs(cDisplay9AMP).^2/n;
    mean_diff_cDisplay9AMP = mean(diff_cDisplay9AMP);

    mean_diff_cDisplay9AMP = abs(mean_diff_cDisplay9AMP);
    mean_diff_cDisplay9AMP = (mean_diff_cDisplay9AMP/max(mean_diff_cDisplay9AMP))*2;
    windowSize = 50; 
%     b = (1/windowSize)*ones(1,windowSize);
    b = ones(1,windowSize);
    for i=1:windowSize
        b(i)=(1/i);
    end
    a = 1;
    
    filter_mean_diff_cDisplay9AMP=filter(b,a,mean_diff_cDisplay9AMP);
    for i2=1:5:24;
        windowSize = 26-i2; 
        b = (1/windowSize)*ones(1,windowSize);
        for i=1:(windowSize)
            b(round(i))=1-exp(-i/windowSize);%1/i;
        end
      b=flip(b);
%         normalize(b,'range',[0 1])
        b=b/sum(b);
        
        

        filter_mean_diff_cDisplay9AMP = filter(b,a,filter_mean_diff_cDisplay9AMP);
    end
    
    filter_mean_diff_cDisplay9AMP=circshift(filter_mean_diff_cDisplay9AMP,-30);
    filter_mean_diff_cDisplay9AMP = filter_mean_diff_cDisplay9AMP/max(filter_mean_diff_cDisplay9AMP);
    wname = 'dmey';
    level = 5;
    sorh = 'h';    % Specified soft or hard thresholding
    thrSettings =  [...
    0.010923547764630 ; ...
    0.026477950363056 ; ...
    0.068700757278239 ; ...
    0.456951311275025 ; ...
    1.276905288740888   ...
    ];

% Denoise using CMDDENOISE.
%--------------------------
% sigDEN = cmddenoise(mean_diff_cDisplay9AMP,wname,level,sorh,NaN,thrSettings);
%     x=1:size(mean_diff_cDisplay9AMP,2);
%     plot(x,mean_diff_cDisplay9AMP,'r-',x,highpass(x,0.1),'g-',x,filter_mean_diff_cDisplay9AMP,'b--');
%     plot(x,highpass(filter_mean_diff_cDisplay9AMP,0.01),'r-',x,highpass(filter_mean_diff_cDisplay9AMP,0.001),'g-',x,filter_mean_diff_cDisplay9AMP,'b--');
%     [pks,locs] = findpeaks(mean_diff_cDisplay9AMP,x, 'NPeaks',1,'SortStr','descend', ...
%                            'MinPeakProminence',1,'MinPeakDistance',6);
%     text(locs+.02,pks,num2str((1:numel(pks))'));
end



function [diff_cDisplay9AMP]=flowAMP2(cDisplay9AMP)
    
    [filter_mean_diff_cDisplay9AMP]=flowAMP(cDisplay9AMP);
%    normalize(highpass(flowAMP(cDisplay9AMP),0.01),'range',[0 1]);
%     dHeight=height(cDisplay9AMP);   dLength=length(cDisplay9AMP);
    [dHeight, dLength]=size(cDisplay9AMP);
    cDisplay9AMP = abs(cDisplay9AMP).^2/dLength;
    diff_cDisplay9AMP(dHeight,dLength)=0;
    
%     fig2=figure('Position',[0 0 3840 500]);      % fig.WindowStyle='modal';
    for diffFreq=1:dHeight
        tic;
        diff_cDisplay9AMP(diffFreq,:)= normalize(highpass(singleFreqFilter(cDisplay9AMP(diffFreq,:)),0.01),'range',[0 1]);
        
%         x=1:size(filter_mean_diff_cDisplay9AMP,2);
%         figure(fig2);
%         plot(x,highpass(filter_mean_diff_cDisplay9AMP,0.01),'r-',x,highpass(singleFreqFilter(cDisplay9AMP(diffFreq,:)),0.01) ,'b-');%,x,filter_mean_diff_cDisplay9AMP,'b--');
%         drawnow;
        disp(['time:',num2str(toc),'      frequency number:',num2str(diffFreq)]);
    end
%     close fig2;

    function [filter_mean_diff_cDisplay9AMP]=singleFreqFilter(mean_diff_cDisplay9AMP)  %filter_mean_diff_cDisplay9AMP

        mean_diff_cDisplay9AMP = abs(mean_diff_cDisplay9AMP);
        mean_diff_cDisplay9AMP = (mean_diff_cDisplay9AMP/max(mean_diff_cDisplay9AMP))*2;
        windowSize = 50; 
        b = ones(1,windowSize);
        for i=1:windowSize; b(i)=(1/i); end
        a = 1;

        filter_mean_diff_cDisplay9AMP=filter(b,a,mean_diff_cDisplay9AMP);
        for i2=1:5:24
            windowSize = 26-i2; 
            b = (1/windowSize)*ones(1,windowSize);
            for i=1:(windowSize); b(round(i))=1-exp(-i/windowSize); end
            b=flip(b); b=b/sum(b);
            filter_mean_diff_cDisplay9AMP = filter(b,a,filter_mean_diff_cDisplay9AMP);
        end

        filter_mean_diff_cDisplay9AMP=circshift(filter_mean_diff_cDisplay9AMP,-30);
        filter_mean_diff_cDisplay9AMP = filter_mean_diff_cDisplay9AMP/max(filter_mean_diff_cDisplay9AMP);

    %     x=1:size(mean_diff_cDisplay9AMP,2);
    %     plot(x,mean_diff_cDisplay9AMP,'r-',x,highpass(x,0.1),'g-',x,filter_mean_diff_cDisplay9AMP,'b--');
    %     plot(x,highpass(filter_mean_diff_cDisplay9AMP,0.01),'r-',x,highpass(filter_mean_diff_cDisplay9AMP,0.001),'g-',x,filter_mean_diff_cDisplay9AMP,'b--');
    %     [pks,locs] = findpeaks(mean_diff_cDisplay9AMP,x, 'NPeaks',1,'SortStr','descend', ...
    %                            'MinPeakProminence',1,'MinPeakDistance',6);
    %     text(locs+.02,pks,num2str((1:numel(pks))'));
    end

end

% ffmpeg -ss 22 -t 10 -i '/media/niv/New Volume/drive_E_backup/Tones and I - DanceMomkey.wav'     '/media/niv/New Volume/drive_E_backup/DanceMomkey_shortversion.wav'


% ffmpeg -i Layla.mj2  -i '/media/niv/New Volume/drive_E_backup/Layla -Eric Clapton [Lyrics].wav' -strict -2 -shortest  test_layla.mp4
%   ffmpeg -i /home/niv/DanceMomkey.mj2  -i '/media/niv/New Volume/drive_E_backup/DanceMomkey_shortversion.wav'  -strict -2  -aspect 16:9 -filter:v scale=3840:2160 -c:v libx264 -preset slow -crf 10  -c:a copy   -shortest    test_DanceMomkey.mov  -y   ; cp test_DanceMomkey.mov   /home/niv/Desktop/test_DanceMomkey.mov



