function  [h3]=piperecord11_LE(Fs,y,cDisplay9AMP,cDisplay9PHAZ,xDisplay,yDisplay,myjet,Freq, theta, Radius)

    global  mtheta; mtheta=theta;
    global  mRadius; mRadius=Radius;
    
     [h3]=initializeTube(Fs,y,myjet,Freq,cDisplay9AMP);
     playloop(cDisplay9AMP,h3);

end


function [h3]=initializeTube(Fs,y,myjet,Freq,cDisplay9AMP)
    global ah R fig ts m C mtheta u v

    global fs;  fs=Fs;    global dt; dt = 1/fs;
    global FrameNumberPerSecond;    FrameNumberPerSecond=60;
    global dFrame; dFrame=1/FrameNumberPerSecond;
    global m; m=dFrame/dt;
    global TotalSample; [TotalSample ,~]=size(y(:,1));  %Song.TotalSample; 
    global TotalFrameNumber; TotalFrameNumber=round(TotalSample/m);
    global FreqIndex; FreqIndex=length(Freq);

    set(0,'defaultfigurecolor',[0 0 0]);
    fig=figure('Position',[0 0 1920 1080]);    fig.MenuBar='none';    fig.Position=[0 0 1920 1080];    % fig.WindowState='fullscreen'; % fig.WindowStyle='modal';
    % create an axes that spans the whole gui
    ah = axes('unit', 'normal', 'position', [0 0 1 1]);


%     SetSteadyBackGroundPhoto    
    set(gca,'handlevisibility','off', 'Visible','off');


    InerCircel=61;    R=linspace(0,2*pi,InerCircel);    [u,v]=meshgrid(mtheta,R);
    tsul=flip(u).*(0.01+0.0015*cDisplay9AMP(:,201)');
    x=(mtheta+(tsul).*cos(v)).*cos(u);    y=(mtheta+(tsul).*cos(v)).*sin(u);    z=(flip(mtheta))+(tsul).*(sin(v))-50;
    C=zeros(InerCircel,FreqIndex,3);
    for i=1:InerCircel;        C(i,:,:)=myjet(:,:);    end
    disp(['C:   ',num2str(length(myjet))]);
    
    set(gca,'NextPlot','add');    h3 = mesh(gca,x,y,z,C,'EdgeColor','interp', 'FaceColor','none','FaceLighting','gouraud');

    
    colormap(1-myjet);
    BL=75;    xlim([-BL BL]);    ylim([-BL BL]);    zlim([-55 45]);    view(270, 90);

    camlight HEADLIGHT;    lighting phong;%     h3.FaceAlpha='flat';%     h3.AlphaData=h3.ZData;%     disp(['h3.ZData:',num2str(max(h3.ZData))])
    set(gca, 'color', [0 0 0]);    set(gca,'xtick',[],'ytick',[],'ztick',[]);
    set(gca,'ZColor',[0 0 0]);    set(gca,'YColor',[0 0 0]);    set(gca,'XColor',[0 0 0]);%     v1 = get(h3,'FaceColor');   
    h3.AmbientStrength=0.4;    h3.EdgeAlpha=1;


    set(gca,'NextPlot','add');    ts = textscatter3(gca,[0 0 0]," ");    set(gca, 'Visible','off');


    function SetSteadyBackGroundPhoto
            % import the background image and show it on the axes
            bgp = imread('/media/niv/New Volume/drive_E_backup/background/casey.jpg');% image(bg);
            imagesc(bgp);
            %     bg = imresize(bg, [1280, 720]); image(bg);
            % prevent plotting over the background and turn the axis off
            set(ah,'handlevisibility','off','visible','off')
            % making sure the background is behind all the other uicontrols
            uistack(ah, 'bottom');
    end
end


function playloop(cDisplay9AMP,h3)
    global dFrame TotalFrameNumber  FrameNumberPerSecond ah  R  ts m C mtheta u v

    % Prepare the new file.
    videoFWriter = vision.VideoFileWriter('/home/niv/YA_HABIBI.mj2','FileFormat','MJ2000','FrameRate',FrameNumberPerSecond);   %,'AudioInputPort',true

    [filter_mean_diff_cDisplay9AMP,mean_diff_cDisplay9AMP]=flowAMP(cDisplay9AMP);%     Temp_filter_mean_diff_cDisplay9AMP = round(normalize(filter_mean_diff_cDisplay9AMP,'range',[0 FreqIndex]));
    filter_mean_diff_cDisplay9AMP = normalize(filter_mean_diff_cDisplay9AMP,'range',[0.5 2.5]);
    
    global bg bgl_real bgw_real bg_l bg_w;  %     SetBackGroundPhoto;


    % RadialWave initialize parameters (zz)
    u_min=min(u,[],'all');    u_max=max(u,[],'all');    u_range=u_max-u_min;
    V0=4.7124;    k=1;    omega=(2*(pi));    phaz=0; lmda=0;
    % CameraMotion initialize parameters
    daz=0.3;    az =270;
    del=0.05;    el = 39.95+del;        el_max=30.95;  el_min=5.95;
    % ObjectColor initialize parameter
    maxWhite=0;
    % tracking initialize parameter
    sample=0;    t = 0;    RecordSemple=0;% 60*m*60*2.5;

    while ( sample<(TotalFrameNumber-4))  % == whilecondition);  % & sample<100
                                        tic;    RecordSemple=RecordSemple+m;    sample=round(RecordSemple/m);    t = t+dFrame;        sample_test=sample;

                                        SetRadialWave;
                                        SetObjectColor;

                                        tsul=flip(u).*(0.0001+0.0015*cDisplay9AMP(:,sample)');  
                                        xx=(mtheta+(tsul).*cos(v));
                                        yy=(mtheta+(tsul).*cos(v));
                                        zz=(2.*sin(phaz+(u-u_min).*(lmda/u_range)))+(tsul).*(sin(v))-40+(10*cos((pi/180)*el));
                                        cc=C-flip(u).*(0.01)+flip(u).*(0.001*cDisplay9AMP(:,sample)')./maxWhite;

                                        h3.XData=xx.*cos(u+pi/2);
                                        h3.YData=yy.*sin(u+pi/2);
                                        h3.ZData=zz;
                                        h3.CData=cc;

                                        SetTextData
                                        SetCameraMotion

                                        F=getframe(gcf);%1280 720%,[0 0 1920 1080]
                                        step(videoFWriter,(F.cdata ));  %,(y((m*(sample-1)+1):(m*sample)+0,:))
                                        time = toc;
                                        disp(['time:',num2str(time),'     sample:',num2str(sample),'     az:',num2str(az),'     el:',num2str(el),'     del:',num2str(del),'     ts.ZData:',num2str(ts.ZData) ]);    %,'     tsul:',num2str(max(flip(u).*(0.0015*cDisplay9AMP(:,sample)'),[],'all'))

    end

    delete(h3);    release(videoFWriter);    close all;



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
        speed=70*dFrame;
        Xt=speed*filter_mean_diff_cDisplay9AMP(sample); %cos(((2*pi)/(60*10))*mod(sample,60*10));
        phaz=omega*(t+Xt)*(-1);
        
        %  disp(['     phaz:',num2str(phaz),'     Xt:',num2str(Xt)]);
       %   disp(['     t:',num2str(t),'     sample:',num2str(sample),'     AMP:',num2str(2),'  T/dFr',num2str(T/dFrame),'    omega:',num2str(omega),'    k:',num2str(k),'    f:',num2str(f),'  Vg:',num2str(Vg),'  V0:',num2str(V0),'  V:',num2str(V),'   lmda:',num2str(lmda)]);
    end     
    function SetTextData
        ts.TextData=string(['#',num2str(sample)]);       %string(Xt);
        Temp=round(filter_mean_diff_cDisplay9AMP(sample));
        ts.ColorData= [C(1,Temp,1) C(1,Temp,2) C(1,Temp,3)];
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
        newcp = cpos - (0.45-0.20*sin((pi/180)*el))*(cpos - ctarg);
        set(gca,'CameraPosition',newcp+[0 0 0]);
%           set(gca,'CameraTarget',[20 0 0])
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
sigDEN = cmddenoise(mean_diff_cDisplay9AMP,wname,level,sorh,NaN,thrSettings);
%     plot(1:12557,mean_diff_cDisplay9AMP,'r-',1:12557,sigDEN,'g-',1:12557,filter_mean_diff_cDisplay9AMP,'b--');
end


% ffmpeg -ss 22 -t 10 -i '/media/niv/New Volume/drive_E_backup/Tones and I - DanceMomkey.wav'     '/media/niv/New Volume/drive_E_backup/DanceMomkey_shortversion.wav'


% ffmpeg -i Layla.mj2  -i '/media/niv/New Volume/drive_E_backup/Layla -Eric Clapton [Lyrics].wav' -strict -2 -shortest  test_layla.mp4
%   ffmpeg -i /home/niv/DanceMomkey.mj2  -i '/media/niv/New Volume/drive_E_backup/DanceMomkey_shortversion.wav'  -strict -2  -aspect 16:9 -filter:v scale=3840:2160 -c:v libx264 -preset slow -crf 10  -c:a copy   -shortest    test_DanceMomkey.mov  -y   ; cp test_DanceMomkey.mov   /home/niv/Desktop/test_DanceMomkey.mov



