echo 'start crop the wav file'
C:\FFmpeg\bin\ffmpeg -y -ss 14 -t 30 -i "D:\drive_E_backup\Tones and I - DanceMomkey.wav"     "D:\drive_E_backup\DanceMomkey_shortversion.wav"

#echo start Extreme cooling
#sudo /usr/bin/ec4Linux.py enable

echo start running sound8_LEF
matlab -batch sound8_LEF

echo start ffmpeg sound8_LEF
C:\FFmpeg\bin\ffmpeg -i N:\mat\Project\Mesh\DanceMomkey2.mj2  -i "D:\drive_E_backup\Tones and I - DanceMomkey.wav"  -strict -2  -aspect 16:9 -filter:v scale=2560:1440 -c:v libx264 -preset slow -crf 10  -c:a copy   -shortest    N:\mat\Project\Mesh\test_DanceMomkey.mov  -y  
# 3840:2160 , 1280:720

#Merge two videos with transparency in ffmpeg
ffmpeg    -i "C:\Users\dvirn\Videos\Los Emigrantes-Ayelet Chen.mp4"  -i  "C:\Users\dvirn\Videos\2021-03-18-2010-38.mp4" -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=480x360[top];   [1:v]setpts=PTS-STARTPTS, scale=480x360, format=yuva420p,colorchannelmixer=aa=0.5[bottom];   [top][bottom]overlay=shortest=1"  -acodec  aac -vcodec libx264 C:\Users\dvirn\Videos\out.mp4

ffmpeg -loop 1 -i image.jpg -i audio.wav -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -shortest out.mp4

#echo start copyng avi
#cp test_DanceMomkey.mov   N:\mat\Project\Mesh\test_DanceMomkey.mov

#echo stop Extreme cooling
#sudo /usr/bin/ec4Linux.py disable

ffmpeg -y -i fallon.mp4 -i van-damme.mp4  \
   -filter_complex \
     "[0:v:0]pad=1920:360[frame];         
      [frame][1:v:0]overlay=640:0[v1];
      [1:v]colorkey=0x008000:0.2:0.2[v2];
      [0:v:0][v2]overlay[v3];
      [v1][v3]overlay=1280:0[v4];
      [v4]scale=960:180[v];
      [0:a:0][1:a:0]amerge=inputs=2[a]" \
   -map "[v]" -map '[a]' \
   -ac 2 -t 0:0:20 \
   green-screen-eliminated.mp4

#Replace green-screen(Black) background on another video
ffmpeg -y -i  LosEmigrantesAyeletChen.mp4 -i Faded1s.mov   -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=1920x1080[top];   [1:v]setpts=PTS-STARTPTS, scale=1920x1080, format=yuva420p,colorkey=0x000000:0.2:0.2[bottom];   [top][bottom]overlay=shortest=1"  -acodec  aac -vcodec libx264 -t 0:1:0   out.mp4

ffmpeg -y -i  "D:\drive_E_backup\background\alb_watfx0308_1080p.mp4" -i Faded1s.mov   -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=1920x1080[top];   [1:v]setpts=PTS-STARTPTS, scale=1920x1080, format=yuva420p,colorkey=0x000000:0.2:0.2[bottom];   [top][bottom]overlay=shortest=0" -map 1:1 -acodec  aac -vcodec libx264   out.mp4


ffmpeg -y   -stream_loop 3 -i  "D:\drive_E_backup\background\video_preview_h264.mp4" -i Faded1s.mov   -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=1920x1080[bottom];   [1:v]setpts=PTS-STARTPTS, scale=1920x1080, format=yuv444p,fps=60,colorkey=0x000000:0.08:0.08[top];   [bottom][top]overlay=shortest=0, fps=60" -map 1:1 -acodec  aac -vcodec libx264  -t 0:0:10 out.mp4


ffmpeg -y   -stream_loop 3 -i  "D:\drive_E_backup\background\The Ice Cave - Drone video from an Icelandic Ice Cave-4_1sZSiDdqw.mkv" -i "N:\mat\Project\Mesh\TheLonelyShepherd2s.mov"   -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=1920x1080[bottom];   [1:v]setpts=PTS-STARTPTS, scale=1920x1080, format=yuv444p,fps=60,colorkey=0x000000:0.08:0.08[top];   [bottom][top]overlay=shortest=0, fps=60" -map 1:1 -acodec  aac -vcodec libx264  out.mp4


ffmpeg -y  -i  "D:\drive_E_backup\background\The Ice Cave - Drone video from an Icelandic Ice Cave-4_1sZSiDdqw.mkv" -ss 85 -i "N:\mat\Project\Mesh\TheLonelyShepherd2.mov"   -filter_complex "  [0:v]setpts=PTS-STARTPTS, scale=1920x1080[bottom];   [1:v]setpts=PTS-STARTPTS, scale=2560x1440, format=yuv444p,fps=60,colorkey=0x000000:0.08:0.08[top];   [bottom][top]overlay=shortest=0, fps=60" -map 1:1 -acodec  aac -vcodec libx264  out2.mp4

youtube-dl.exe https://youtu.be/4_1sZSiDdqw

youtube-dl -f bestvideo  --postprocessor-args "-ss 0:0:30 -to 0:6:22" https://www.youtube.com/watch?v=t-gTc7lRbfc


youtube-dl.exe -f bestaudio  https://www.youtube.com/watch?v=CqvSY3Hnij4
ffmpeg -i  "HAUSER - Wicked Game-0C-dNgypA5M.webm"  -c:a pcm_f32le "HAUSER - Wicked Game.wav"

# Downmix each input into specific output channel
ffmpeg -i out6.mov -i second.m4a -filter_complex "[0][1]amerge=inputs=2,pan=stereo|FL<c0+c1|FR<c2+c3[a]" -map "[a]" output.wav


ffmpeg -i input.mp4 -vf "hue=s=0" output.mp4



system(['C:\FFmpeg\bin\ffmpeg -i "D:\drive_E_backup\Sea cave ambience _ Calming seashore sounds for sleep and relaxation _ 4K SOUNDSCAPE-t-gTc7lRbfc.webm" ' ...
        '  -i "D:\drive_E_backup\Sea cave ambience _ Calming seashore sounds for sleep and relaxation _ 4K SOUNDSCAPE-t-gTc7lRbfc.temp.m4a"  -strict -2  -aspect 16:9 ',...
        ' -filter:v   scale=2560:1440   -c:v libx264 -preset ',...
        'slow -crf 10  -c:a pcm_f32le   -shortest  "D:\drive_E_backup\',...
        'SeaCaveAmbience.mov"  -y'])
system(['C:\FFmpeg\bin\ffmpeg -i "D:\drive_E_backup\SeaCaveAmbience.mov" -vf "hue=s=0"    ' ...
        '"D:\drive_E_backup\SeaCaveAmbience.mp4"  -y'])

yt-dlp --verbose -f "(bestvideo+bestaudio/best)[protocol!*=dash]" --external-downloader ffmpeg --external-downloader-args "ffmpeg_i:-ss 02:01:00 -to 02:05:00 " "https://www.youtube.com/watch?v=M2UwyZ_1v38"


ffmpeg -y  -i GalaxyTraversal.webm  -map 0:0   GalaxyTraversal.mp4


