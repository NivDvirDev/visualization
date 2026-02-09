function  [h3]=piperecord11_LEF(SongTag,Fs,y,cDisplay9AMP,myFileFullName,xDisplay,yDisplay,myjet,Freq, theta, Radius)

    global  mtheta; mtheta=theta;
    global  mRadius; mRadius=Radius;
    
     [h3]=initializeTube(Fs,y,myjet,Freq,cDisplay9AMP);
     playloop(SongTag,y,cDisplay9AMP,Freq,h3,myFileFullName);

end


function [h3]=initializeTube(Fs,y,myjet,Freq,cDisplay9AMP)
    global ah R fig ts C mtheta u v

    global fs;  fs=Fs;    global dt; dt = 1/fs;
    global FrameNumberPerSecond;    FrameNumberPerSecond=60;
    global dFrame; dFrame=1/FrameNumberPerSecond;
    global m; m=dFrame/dt;
    global TotalSample; [TotalSample ,~]=size(y(:,1));  %Song.TotalSample; 
    global TotalFrameNumber; TotalFrameNumber=round(TotalSample/m);
    global FreqIndex; FreqIndex=length(Freq);


    set(0,'defaultfigurecolor',[0 0 0]);
    fig=figure('Position',[0 0 1920 1080]);    fig.MenuBar='none';    fig.Position=[0 0 1920 1080];    % fig.WindowState='fullscreen'; % fig.WindowStyle='modal';
    fig.WindowState='minimized';
    % create an axes that spans the whole gui
    ah = axes('unit', 'normal', 'position', [0 0 1 1]);


%     SetSteadyBackGroundPhoto    
    set(gca,'handlevisibility','off', 'Visible','off');


    InerCircel=60;    R=linspace(-pi,pi,InerCircel);    [u,v]=meshgrid(mtheta,R);
    tsul=flip(u).*(0.01+0.0015*cDisplay9AMP(:,21)');
    x=(mtheta+(tsul).*cos(v)).*cos(u);    y=(mtheta+(tsul).*cos(v)).*sin(u);    z=(flip(mtheta))+(tsul).*(sin(v))-50;
    C=zeros(InerCircel,FreqIndex,3);
    for i=1:InerCircel;        C(i,:,:)=myjet(:,:);    end
    disp(['C:   ',num2str(length(myjet))]);
    
    set(gca,'NextPlot','add');    h3 = mesh(gca,x,y,z,C,'EdgeColor','interp', 'FaceColor','none','FaceLighting','gouraud');

    
    colormap(1-myjet);
    BL=75;    xlim([-BL BL]);    ylim([-BL BL]);    zlim([-75 45]);    view(270, 90);

    camlight HEADLIGHT;    lighting phong;%     h3.FaceAlpha='flat';%     h3.AlphaData=h3.ZData;%     disp(['h3.ZData:',num2str(max(h3.ZData))])
    set(gca, 'color', [0 0 0]);    set(gca,'xtick',[],'ytick',[],'ztick',[]);
    set(gca,'ZColor',[0 0 0]);    set(gca,'YColor',[0 0 0]);    set(gca,'XColor',[0 0 0]);%     v1 = get(h3,'FaceColor');   
    h3.AmbientStrength=0.4;    h3.EdgeAlpha=1;


    set(gca,'NextPlot','add');    ts = textscatter3(gca,[0 0 0],"  ");
    ts.FontName='Cambria';
    set(gca, 'Visible','off');


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
end


function playloop(SongTag,y,cDisplay9AMP,Freq,h3,myFileFullName)
    global dFrame TotalFrameNumber  FrameNumberPerSecond ah  R  ts m C mtheta u v

    % Prepare the new file.
    videoFWriter = vision.VideoFileWriter(['N:\mat\Project\Mesh\',SongTag,'.mj2'],'FileFormat','MJ2000','FrameRate',FrameNumberPerSecond);   %,'AudioInputPort',true

    [filter_mean_diff_cDisplay9AMP,mean_diff_cDisplay9AMP]=flowAMP(cDisplay9AMP);%     Temp_filter_mean_diff_cDisplay9AMP = round(normalize(filter_mean_diff_cDisplay9AMP,'range',[0 FreqIndex]));
    filter_mean_diff_cDisplay9AMP = normalize(filter_mean_diff_cDisplay9AMP,'range',[0.5 2.5]);
    
    global bg bgl_real bgw_real bg_l bg_w;  %     SetBackGroundPhoto;

    jf=java.text.DecimalFormat;
    % RadialWave initialize parameters (zz)
    u_min=min(u,[],'all');    u_max=max(u,[],'all');    u_range=(u_max-u_min)/2;
    V0=4.7124;    k=1;    omega=(2*(pi));    phaz=0; lmda=0;
    % CameraMotion initialize parameters
    daz=0.3;    az =270;
    del=0.05;    el = 39.95+del;        el_max=30.95;  el_min=9.95;
    PeriodicWave=@(t1) heaviside(mod(t1, 6*pi)-4*pi).*sin(mod(t1, 2*pi));
    iso226ForFreq(size(cDisplay9AMP,1))=0;
    for i=1:1:size(cDisplay9AMP,1); iso226ForFreq(i)=(iso226(40,Freq(i))/20); end
    maxIso226=1+max(iso226ForFreq,[],'all');
    % ObjectColor initialize parameter
    maxWhite=0;
    folder = 'N:\mat\Project\Mesh';
    % tracking initialize parameter
    global matObj PackIdx Packet FileName Packets matObjLen InitialSampleGap
    InitialSampleGap =load(fullfile(folder,'myFile001.mat')).cDisplay3PHAZ.OpenPack_sample;
    sample=0+InitialSampleGap;    t = 0;    RecordSemple=m*sample;  %60*m*12.5;% 60*m*60*2.5;
    matObjLen=30;
    FileName = (['myFile',sprintf('%02i',floor(sample./1000)),'1.mat']);
    myFileFullName = fullfile(folder,FileName);
    matObj = matfile(myFileFullName);
    Packets=[]; matObjLen=length(matObj.cDisplay3PHAZ);
    for i=1:matObjLen
        Packet=(matObj.cDisplay3PHAZ(1,i));
        if ~isempty(Packet.Precord); Packets=[Packets;Packet.Precord]; end
    end
    Packet = (matObj.cDisplay3PHAZ(1,(floor(sample./100)+1)));
    PackIdx = mod(sample-3,100);    if (PackIdx==0); PackIdx=100; end




    while ( sample<round((TotalFrameNumber)-26))  % == whilecondition);  % & sample<100
                                        tic;    RecordSemple=RecordSemple+m;    sample=round(RecordSemple/m);    t = t+dFrame;        sample_test=sample;

                                        
%                                         h3.XData=zeros(size(h3.XData));
%                                         h3.YData=zeros(size(h3.YData));
%                                         h3.ZData=zeros(size(h3.ZData));
%                                         h3.CData=zeros(size(h3.CData));
                                        
                                        
                                        [uV sV] = memory;
                                        disp(['sample:',num2str(sample),'     sV.PhysicalMemory.Available:',char(jf.format(sV.PhysicalMemory.Available))]);
                                        SetRadialWave;
                                        SetObjectColor;
                                        UpdatePointer(sample)
                                        disp(['sample:',num2str(sample),'     PackIdx: ',num2str(PackIdx),'     Packet:',num2str(Packet.Precord),'     FileName:',FileName]);
                                        A3=(find(Packet.data(PackIdx,:,:)==max(Packet.data(PackIdx,:,:),[],2)));
                                        A4=circshift( Packet.data(PackIdx,1:size(cDisplay9AMP,1),:) , -1*A3);
%                                         tsul=8*flip(u).*(((0.0003*cDisplay9AMP(:,sample)'))+...
%                                                         (0.00288.*fillmissing(real(squeeze(A4)).^1,'constant',0)'));  %
                                        tsul=(maxIso226-iso226ForFreq(:))'.*flip(u).*(((0.0003*cDisplay9AMP(:,sample)'))+...
                                                        (0.00288.*fillmissing(real(squeeze(A4)).^1,'constant',0)'));

%                                         W=phaz+(u-u_min).*(lmda/u_range);
%                                         PeriodicWave=sin(W);   PeriodicWave(PeriodicWave<0)=0;

                                        draft=ones(size(mean(tsul)))*mean(tsul,'all')*4;
                                        [Draft]=draftTsul(mean(tsul));
                                        xy=(mtheta+Draft+(tsul).*(cos(v)));   %+mean(tsul)*2;   %draft;     %
%                                         yy=(mtheta+(tsul).*(cos(v)));   %+mean(tsul)*2;   %draft;     %                                     
                                        zz=(2.*PeriodicWave(phaz+(u-u_min).*(lmda/u_range)))+(tsul).*sin(v)-40+(10*cos((pi/180)*el))+Draft*(1.6180339887498948482);    %mean(tsul)*2;     %
                                        cc=C-flip(u).*(0.01)+flip(u).*(0.001*cDisplay9AMP(:,sample)')./maxWhite;

                                        clear h3.XData h3.YData h3.ZData h3.CData;
                                        h3.XData=xy.*cos(u+pi/2);    %
%                                         h3.YData=yy.*(sin(u+pi/2)/2);
                                        h3.YData=xy.*sin(u+pi/2);    %+yDraft
                                        
                                        h3.ZData=zz;
                                        h3.CData=cc;
                                        
                                        

                                        %[tsulMax,tsulMaxIdx] = max(tsul,[],'all','linear');
                                        %[tsulMaxIdx tsulMaxIdy]=find(tsul==tsulMax);
                                        textSide=15;%mod(sample,60)+1;
                                        tsXYZ=[h3.XData(textSide,:); h3.YData(textSide,:); h3.ZData(textSide,:)];
                                        tsColor=h3.CData(textSide,:,:);
                                        SetTextData(tsXYZ,normalize(tsColor,'range',[0 1]),textSide)
                                        SetCameraMotion

                                        F=getframe(gcf);%1280 720%,[0 0 1920 1080]
                                        step(videoFWriter,(F.cdata)); %, y((m*(sample-1)+1):(m*sample)+0,:)); 
                                        time = toc;
%                                         disp(['time:',num2str(time),'     sample:',num2str(sample),'     az:',num2str(az),'     el:',num2str(el),'     del:',num2str(del),'     ts.ZData:',num2str(ts.ZData) ]);    %,'     tsul:',num2str(max(flip(u).*(0.0015*cDisplay9AMP(:,sample)'),[],'all'))
                                        
    end

    delete(h3);    release(videoFWriter);    close all;

    
    function [DisplayIntegral]=draftTsul(Radius)
    FreqIndex=length(Radius);
    DisplayIntegral(FreqIndex)=0;
        for i_draft=1:FreqIndex
               DisplayIntegral(i_draft)=(Radius(i_draft)/(1.6180339887498948482))+DisplayIntegral(Back360(i_draft));
        end
   
    function [nextRoll]=forward360(index)
        nextRoll = closestIndex(mtheta(index)+(2*pi),mtheta);
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
        maxWhite=max(flip(u).*(0.001*cDisplay9AMP(:,sample)'),[],'all'); %sample_test
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
        
        
        persistent Solfege;
        if isempty(Solfege)
            Solfege(1).Name='Do';
            Solfege(1).Freqs =[4.088,      8.176,      16.352,     32.703,     65.406,     130.813,     261.626,     523.251,     1046.502,     2093.005,      4186.009];    %,
            Solfege(1).label(length(Solfege(1).Freqs)+1).ts=0;
            
            Solfege(2).Name='Re';
            Solfege(2).Freqs =[4.5885,     9.177,      18.354,     36.708,     73.416,     146.832,     293.665,     587.33,      1174.659,     2349.318,      4698.636];    %,     9397.273,      18794.545];
            Solfege(2).label(length(Solfege(2).Freqs)+1).ts=0;
            
            Solfege(3).Name='Mi';
            Solfege(3).Freqs =[5.150,      10.301,     20.602,     41.203,     82.407,     164.814,     329.628,     659.255,     1318.51,      2637.02,      5274.041];    %,     10548.082,     21096.164];
            Solfege(3).label(length(Solfege(3).Freqs)+1).ts=0;
            
            Solfege(4).Name='Fa';
            Solfege(4).Freqs =[5.456,      10.913,     21.827,     43.654,     87.307,     174.614,     349.228,     698.456,     1396.913,     2793.826,     5587.652];    %,     11175.303,     22350.607];
            Solfege(4).label(length(Solfege(4).Freqs)+1).ts=0;
            
            Solfege(5).Name='Sol';
            Solfege(5).Freqs=[6.125,      12.25,      24.5,       48.999,     97.999,     195.998,     391.995,     783.991,     1567.982	   3135.963,     6271.927];     %,     12543.854,     25087.708];
            Solfege(5).label(length(Solfege(5).Freqs)+1).ts=0;
            
            Solfege(6).Name='La';
            Solfege(6).Freqs =[6.875,     13.75,      27.5,       55,         110,        220,         440,         880,         1760,         3520,         7040];         %,         14080,         28160];
            Solfege(6).label(length(Solfege(6).Freqs)+1).ts=0;
            
            Solfege(7).Name='Si';
            Solfege(7).Freqs =[7.717,      15.434,     30.868,     61.735,     123.471,    246.942,     493.883,     987.767,     1975.533,     3951.066,     7902.133];    %,     15804.266,     31608.531];
            Solfege(7).label(length(Solfege(7).Freqs)+1).ts=0;

        end       
     
        
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
                    Solfege(note).label(octave).ts.FontSize=8+octave*0.5;
                    Solfege(note).label(octave).ts.FontWeight='bold';
                    Solfege(note).label(octave).ts.FontAngle='italic';
                    %tsDo(i).struct('ts',textscatter3(gca,[0 0 0]," "));
                else
                    Solfege(note).label(octave).ts.XData=cDisplayX(octave);
                    Solfege(note).label(octave).ts.YData=cDisplayY(octave);
                    Solfege(note).label(octave).ts.ZData=cDisplayZ(octave);
                    Solfege(note).label(octave).ts.ColorData=abs(cDisplayC(octave,:));
                    %if (sample>(5*60));    Solfege(note).label(octave).ts.TextData=string([" "]);    end
                end
            end
        end
        
        
%         set(gca,'NextPlot','add'); 
%         ts2=textscatter3(gca,[cDisplayX(1) cDisplayY(1) cDisplayZ(1)],string([num2str(Do(iDo)),'Hz']));
%         ts2.ColorData= [C(1,Temp,1) C(1,Temp,2) C(1,Temp,3)];
       % set(gca, 'Visible','off');
        
%             tsDo(iDo).TextData=string([num2str(Do(iDo)),'Hz']);
%             tsDo(iDo).ColorData= [C(1,Temp,1) C(1,Temp,2) C(1,Temp,3)];
            %tsDo(iDo)=textscatter3(gca,[cDisplay(1,closestIndex(iDo)) cDisplay(2,closestIndex(iDo)) cDisplay(3,closestIndex(iDo))],[num2str(round(Do(iDo)))]);

    end
    function SetCameraMotion 

            if (el >= el_max)
                del=abs(del)*(-1);
            end
            if (el <=el_min)
                del=abs(del)*(1);
            end
            if (sample >= (TotalFrameNumber-4)/2)  % (TotalFrameNumber-4)/2);
                el = el+del*cos(pi*el/180);
                az = az-daz;
            else
                az = az-daz;
                el=el_max-0.90+del;
            end
            %         el = el+del;%*cos(pi*el/180)

%          if (az >= 300);
%             daz=daz*(-1);
%         end
%         if (az <= 240);
%             daz=daz*(-1);
%         end

%         el=90;            %19.95;
        view( az, el);
%         view( 180*sin(el), 90*abs(el));
%         zoom('off');
         teta_0to1=((el-(el_min+del))/(el_max-el_min));

         
        global isBackGroundPhoto
        if (isBackGroundPhoto==true)
                bg_x=0;
                bgy_horizon=floor(bgl_real/3);
                bgy_scale=(bgl_real-bgy_horizon)-bg_l;
                
                bg_y=bgy_horizon+round(teta_0to1*bgy_scale);   %round(bgw_real/2)+sample*3;
                imagesc(ah,bg( (1+bg_y):min(bg_l+bg_y,bgl_real),(1+bg_x):(bg_w+bg_x),: ));
        end
        
        set(gca,'CameraTarget',[-1 -1 -5-30*teta_0to1]);
        ts.ZData=-5-30*teta_0to1;

       
        set(gca,'CameraViewAngleMode','manual');
        ctarg = get(gca,'CameraTarget');
        cpos = get(gca,'CameraPosition');
        newcp = cpos - (0.66-0.20*sin((pi/180)*el))*(cpos - ctarg);
        set(gca,'CameraPosition',newcp+[0 0 0]);
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
% % sigDEN = cmddenoise(mean_diff_cDisplay9AMP,wname,level,sorh,NaN,thrSettings);
%     x=1:size(mean_diff_cDisplay9AMP,2);
%     plot(x,mean_diff_cDisplay9AMP,'r-',x,sigDEN,'g-',x,filter_mean_diff_cDisplay9AMP,'b--');
%     [pks,locs] = findpeaks(mean_diff_cDisplay9AMP,x, 'NPeaks',1,'SortStr','descend', ...
%                            'MinPeakProminence',1,'MinPeakDistance',6);
%     text(locs+.02,pks,num2str((1:numel(pks))'));
end


% ffmpeg -ss 22 -t 10 -i '/media/niv/New Volume/drive_E_backup/Tones and I - DanceMomkey.wav'     '/media/niv/New Volume/drive_E_backup/DanceMomkey_shortversion.wav'


% ffmpeg -i Layla.mj2  -i '/media/niv/New Volume/drive_E_backup/Layla -Eric Clapton [Lyrics].wav' -strict -2 -shortest  test_layla.mp4
%   ffmpeg -i /home/niv/DanceMomkey.mj2  -i '/media/niv/New Volume/drive_E_backup/DanceMomkey_shortversion.wav'  -strict -2  -aspect 16:9 -filter:v scale=3840:2160 -c:v libx264 -preset slow -crf 10  -c:a copy   -shortest    test_DanceMomkey.mov  -y   ; cp test_DanceMomkey.mov   /home/niv/Desktop/test_DanceMomkey.mov



