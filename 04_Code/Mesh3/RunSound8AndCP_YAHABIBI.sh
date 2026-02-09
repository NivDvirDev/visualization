echo 'start crop the wav file'
ffmpeg -y -ss 35 -t 230 -i '/media/niv/New Volume/drive_E_backup/YA HABIBI.wav'     '/media/niv/New Volume/drive_E_backup/YA_HABIBI_shortversion.wav'

#echo start Extreme cooling
#sudo /usr/bin/ec4Linux.py enable

echo start running sound8_LE
sudo -u niv matlab -batch sound8_LE

echo start ffmpeg sound8_LE
ffmpeg -i /home/niv/YA_HABIBI.mj2  -i '/media/niv/New Volume/drive_E_backup/YA_HABIBI_shortversion.wav'  -strict -2  -aspect 16:9 -filter:v scale=2560:1440 -c:v libx264 -preset slow -crf 10  -c:a copy   -shortest    test_YA_HABIBI.mov  -y  
# 3840:2160 , 1280:720


echo start copyng avi
cp test_YA_HABIBI.mov   /home/niv/Desktop/test_YA_HABIBI.mov

#echo stop Extreme cooling
#sudo /usr/bin/ec4Linux.py disable
