# /usr/env/bin python3
import os
import sys
from decimal import Decimal
import binascii

class MergeVideo(object):
    """
    合并 flv 格式视频
    """

    def int_b2a(self, string):
        return int(binascii.b2a_hex(string), 16)

    def int2hex(self,e_list):        
        return int(''.join("%0*X" % (2,d) for d in e_list),16)

    def bin2double(self, int_string : int) -> str:  
        '''
        模拟浮点数据从内存的取出过程
        二进制转浮点(double) 的计算公式 ： 
        V = (-1)^(S) * (1.M) * 2^(I-1023)[V 为 value 数值，
        S 为 符号(取 0或1)，M 为尾数，I 是指数]
        '''
        int_string = int(int_string)
        #  转成二进制
        bin_string = ''.join(bin(int_string))  
        #  由于python中二进制数前有 “0b” ，所以将其进行分割，取数值部分
        bin_string = bin_string[2:]  
        # 目的是想转换成 double 类型，double 是 8 字节 64 位，所以判断下长度然后补全 64 位。
        if len(bin_string) <= 64:  
            add_zero_count = 64 - len(bin_string)
            bin_string = "0"*add_zero_count + bin_string
        #  处理符号位
        symbol = int(bin_string[0])
        if symbol == 0:
            symbol = (-1)**0
        elif symbol == 1:
            symbol = (-1)**1
        else:
            print("symbol 不是 int 数值")
        #  处理尾数部分
        #  这52位二进制的尾数部分计算为二进制的小数计算
        #  也就是二进制的每一位乘二的负 N 次方（N的取值为1,2,3,4,5...）,直到2的负52次方为止。
        mantissa = bin_string[12:] 
        mantissa_value = 0
        for n in range(1, 53):
            mantissa_value += int(mantissa[n-1]) * ((1/2)**n)
        #  在储存时 1 被省略，现在需要加上
        mantissa_value = mantissa_value + 1 
        #  指数部分
        index = bin_string[1:12]
        index = int(index, 2)  
        #  得到的值需要减去 1023（偏移值）
        index = 2 ** (index - 1023)
        double_string = symbol * mantissa_value * index
        return double_string


    def double2bin(self, double_string : int) -> str:
        '''
        模拟 double 类型数据的储存过程，得到最后二进制值对应的十六进制数.
        浮点类型转二进制的方法是整数部分和小数部分分开计算，
        整数部分使用除以二取整，小数部分使用乘以二取整.
        '''
        if int(double_string) < 0:
            symbol = '1'
        else:
            symbol = '0' 
        #  为了保证精度，使用 Decimal 函数来显示精度值，转成字符串好整数小数分离
        double_string = str(Decimal(double_string))
        double_string = double_string.split(".")
        #  处理整数部分
        int_part = double_string[0]
        decimal_part = "0." + double_string[1]
        #  将整数部分转换为二进制
        bin_intpart = bin(int(int_part))  
        #  去除"0b"
        bin_intpart = bin_intpart[3:]  
        #  确定整数部分二进制的长度，好计算小数部分需要计算多少位，因为就 52 位的长度
        bin_intpart_len = len(bin_intpart)
        offset = ''.join(bin(1023+bin_intpart_len))
        #  这 "0b" 真恶心
        offset = offset[2:]  
        #  小数部分
        global value
        global bin_decimalpart  # 创建两个 globle 变量，将循环中接收的值传出
        bin_decimalpart = ''
        value = float(decimal_part)
        bin_decimalpart_len = 52 - bin_intpart_len
        #  因为尾数是整数部分的二进制数和小数部分的二进制数组合而成，一共 52 位。
        for n in range(0, bin_decimalpart_len):  
            value = value * 2  
            if value < 1:
                bin_decimalpart = bin_decimalpart + '0'
            else:
                bin_decimalpart = bin_decimalpart + '1'
                value = value - 1
        mantissa = bin_intpart + bin_decimalpart  
        index = offset
        bin_string = symbol + index + mantissa
        return bin_string


    def get_last_ts(self,data : str) -> str:  
        """
        获取到视频文件的最后一帧视频和最后一帧音频的时间戳
        """
        video_timestamp = ''
        audio_timestamp = ''
        pre_tag_len = 4
        while True:
            pre_tag_value = self.int_b2a(data[-pre_tag_len:])
            last_tag = data[-pre_tag_value-pre_tag_len:-pre_tag_len]
            data = data[:-pre_tag_value-pre_tag_len]
            tag_type = binascii.b2a_hex(last_tag[:1])
            #  低位
            timestamp = last_tag[4:7]  
            #  高位，放第一位
            timestamp_ex = last_tag[7:8]  
            if tag_type == b'08':
                if len(audio_timestamp) == 0:
                    #  最后一帧音频时间戳
                    audio_timestamp = '%s' % self.int_b2a(
                        timestamp_ex+timestamp)  
            elif tag_type == b'09':
                if len(video_timestamp) == 0:
                     #  最后一帧视频时间戳
                    video_timestamp = '%s' % self.int_b2a(
                        timestamp_ex+timestamp) 
            if len(audio_timestamp) > 0 and len(video_timestamp) > 0:
                break
        return audio_timestamp, video_timestamp


    def update_timestamp(self, data : str, last_ts : str) -> str:
        '''  
        1.修改第二个视频及以后的时间戳，保证正常播放。所以第二个视频需要叠加第一
            个视频的时间戳、第三个视频需要叠加第二个视频的时间戳，以此类推。
        2.这里需要注意一个问题，时间戳和扩展时间戳的高低位问题：计算的
            时候由于 ts_ex 是高位所以需要将其放在首位，
            反向计算的时候也许要将其放回末尾位置。
        3.解释下为什么只有音频帧(0x08)、视频帧(0x09),而没有脚本帧(0x12) 的修改，
            说实话除了第一个视频需要脚本帧，后续的视频合并的时候只需要内容帧就好了。
        '''
        # last_ts 包含上一个视频的最后一帧视频时间戳、最后一帧音频时间戳
        last_audio_ts, last_video_ts = last_ts 
        tag_list = []
        pre_tag_len = 4
        data = list(data)
        try:
            while True:
                if len(data) <= 13:
                    break
                pre_tag_size = data[-pre_tag_len:]
                pre_tag_value = self.int2hex(pre_tag_size)
                last_tag = data[-pre_tag_value - pre_tag_len:-pre_tag_len]
                #  不开辟新的内存空间,直接在原始数据上边操作
                del data[-pre_tag_value-pre_tag_len:]
                tag_type = last_tag[0]
                #  低位时间戳
                timestamp = last_tag[4:7]
                #  高位，放第一位
                timestamp_ex = last_tag[7:8]
                #  如果是音频帧，就将计算值叠加上一个音频时间戳
                if tag_type == 8:  
                    # 计算十进制下的时间戳
                    audio_timestamp = self.int2hex(timestamp_ex+timestamp)
                    # 十进制下的更新值
                    update_audio_ts = int(last_audio_ts) + audio_timestamp
                    # 16 进制
                    update_audio_ts = hex(update_audio_ts)
                    if len(update_audio_ts) < 10:
                        # 补 0，差几位补几个
                        add_zero_count = 10 - len(update_audio_ts)  
                        update_audio_ts = '0' * add_zero_count + update_audio_ts[2:]
                    move_ts_ex = update_audio_ts[0:2]
                    #  修改工作完成，接下来将此值与原始值替换
                    update_audio_ts = update_audio_ts[2:] + move_ts_ex
                    #  重新转化成列表用来替换
                    timestamp_list =[]
                    for n in range(0,8,2):
                        #  没办法,只能先转成16进制,再转成10进制才成
                        #  bytes() 函数只接受数值类型
                        timestamp_list.append(int(update_audio_ts[n:n+2],16))
                    last_tag[4:8] = timestamp_list
                #  视频中的时间戳更新与上边音频时间戳更新操作一致
                elif tag_type == 9:  
                    #  计算十进制下的时间戳
                    video_timestamp = self.int2hex(timestamp_ex+timestamp)
                    #  十进制下的更新值
                    update_audio_ts = int(last_audio_ts) + video_timestamp  
                    #  16 进制
                    update_audio_ts = hex(update_audio_ts)
                    #  之所以为 10 是因为上边使用 hex() 函数后,字符串多了个"0x"
                    if len(update_audio_ts) < 10:
                        #  补 0，差几位补几个
                        add_zero_count = 10 - len(update_audio_ts)  
                        update_audio_ts = '0' * add_zero_count + update_audio_ts[2:]
                    move_ts_ex = update_audio_ts[0:2]
                    #  修改工作完成，接下来将此值与原始值替换
                    update_audio_ts = update_audio_ts[2:] + move_ts_ex
                    #  重新转化成列表用来替换
                    timestamp_list =[]
                    for n in range(0,8,2):
                        #   bytes() 函数只接受数值类型
                        timestamp_list.append(int(update_audio_ts[n:n+2],16))
                    last_tag[4:8] = timestamp_list
                #  正好一个视频处理完就只有 tag 没有 flv_header
                tag_list.insert(0, last_tag + pre_tag_size)
        except KeyboardInterrupt:
            print("年轻人要有耐心")
            sys.exit()
        #  用列表接收字节值
        flv_body_list =[]
        for data in tag_list[1:]:
            change_bytes = bytes(data)
            flv_body_list.append(change_bytes)
        #  转换成字节串
        flv_body_btyes = b"".join(flv_body_list)
        return flv_body_btyes  


    def get_duration(self, data: str) -> int:
        '''
        计算 duration
        '''
        duration_local = data.index(b"duration")  # 找到 duration 的位置
        #  根据 flv 数据结构，确定 duration 值的位置
        bin_duration_value = data[duration_local+9:duration_local+17]
        #  将二进制的值转换成十六进制 ascii 码 
        b2a_duration_value = binascii.b2a_hex(
            bin_duration_value)  
        #  转换成十进制值，为后续计算出其 double 类型数值
        int_duration_value = int(b2a_duration_value, 16)
        return self.bin2double(int_duration_value)


    def update_duration(self, data: str, duration_list: list) -> str:

        '''
        计算总的视频时长,然后在转换回去二进制形式，用这个总的视频时长值，替换第一个视频的时长值
        '''
        int_sum_duration = sum(duration_list)
        #  转换回十六进制，替换原视频的视频长度值
        hex_sum_duration = hex(int(self.double2bin(int_sum_duration), 2))
        #  去掉‘0x’,准备换回二进制的字节形式，像这样b'/x40/x70...'
        hex_sum_duration = hex_sum_duration[2:]
        a2b_sum_duration = binascii.a2b_hex(hex_sum_duration)
         # 定位 duration 值的位置
        duration_local = data.index(b'duration') 
        # 提取出值
        duration_value = data[duration_local+9:duration_local+17]  
        # 进行替换
        update_data = data.replace(duration_value, a2b_sum_duration, 1)  
        return update_data


    def delete_video(self, path: str, video_list: list):       
        try:
            for time_num in range(1,11):
                sys.stdout.write("\r\033[0;35m{}s 后删除分段视频，如需退出请按 Crtl+C\033[0m"
                    .format(10-time_num))
                sys.stdout.flush()
                time.sleep(1)
        except KeyboardInterrupt:
            print("Have a good day!\n")
            sys.exit()
        print("\n")
        try:  
            for video_nmae in video_list:
                os.system("rm {}{}".format(path,video_nmae))                
        except Exception as e:
            print(e)


    def get_video(self, merge_list = None):      
        video_list = []
        path = (os.popen('pwd').read()).strip('\n') + '/'
        video_path = path + 'Bilivideo'
        if 'Bilivideo' not in os.popen(F'ls {path}').read():
            print(F"Error:未在路径 { path } 找到名为 Bilivideo 的文件夹，请手动添加.")
            sys.exit()
        if merge_list == None:
            video_name = os.popen(F"ls {video_path}").read()
            video_list = (video_name.rstrip('\n')).split('\n')
        else:
            video_list = merge_list
        #  设置合并后的视频名称
        merged_name = ((video_list[0]).split("_"))[0]
        print(
            "[>>>]  合并以下视频:\n\n"+"\n".join(e for e in video_list) + "\n")
        print(
            F"[>>>] 一共 {len(video_list)} 个视频,请核对是否有误\n")
        try:
            while True:
                confirm = input("[>>>]  请输入 y/n\n")
                if  confirm == 'y':
                    print("[>>>]  即将开始合并视频，请耐心等待...")
                    break
                elif confirm == 'n':
                    print("[>>>]  已取消本次合并")
                    sys.exit()
                else:
                    print("[>>>]  请正确输入 y 或者 n,然后回车")
        except KeyboardInterrupt:
            print("Have a good day!\n")
            sys.exit()
        return video_path,video_list,merged_name

    def merge(self, merge_list = None):
        viedo_data_list = list()
        last_ts_list = list()
        duration_list = list()
        video_path,video_list,merged_name = self.get_video(merge_list) 
        #  获取每个视频文件的 duration ，视频 Tag 中的timestamp
        for n in range(0, len(video_list)):
            sys.stdout.write(
                F"\r\033[0;35m正在处理第 {n+1} 个视频, \
                剩余视频数量 {len(video_list) - (n+1)}, 请耐心等待...\033[0m")
            sys.stdout.flush()
            with open(video_path + video_list[n], 'rb') as fileout:
                data = fileout.read()
            if n == 0:
                duration_value = self.get_duration(data)
                # 取出 duration 值，存进列表，一会儿计算总值使用
                duration_list.append(duration_value)
                last_ts_audio, last_ts_video = self.get_last_ts(data)
                last_ts_list.append((last_ts_audio, last_ts_video))
                viedo_data_list.append(data)
            if n > 0:
                duration_value = self.get_duration(data)
                # 取出 duration 值，存进列表，一会儿计算总值使用
                duration_list.append(duration_value)
                last_ts = last_ts_list.pop()
                # 修改时间戳，返回修改后的数据
                flv_body = self.update_timestamp(data, last_ts)  
                # 取出修改完的最后一帧时间戳给下个视频用
                last_ts_audio, last_ts_video = self.get_last_ts(flv_body)  
                last_ts_list.append((last_ts_audio, last_ts_video))
                # flv_body 就是视频数据，只是去掉了 flv_header 和 第一个 tag(脚本帧)
                viedo_data_list.append(flv_body)
        file_path = os.popen('pwd').read()
        make_file = os.popen("ls").read()
        if "merged_video" not in make_file:
            os.system("mkdir merged_video")
        save_path = file_path.strip('\n') + '/merged_video/'
        with open(save_path + merged_name + '.flv', 'wb') as filein:
            for n in range(0, len(viedo_data_list)):
                if n == 0:
                    update_data = self.update_duration(
                        viedo_data_list[n], duration_list)  
                    filein.write(update_data)
                else:
                    filein.write(viedo_data_list[n])
        tip_message = F"\n文件已储存在 {save_path}{merged_name}"
        print(tip_message)
        self.delete_video(video_path, video_list)


def main():
    mv = MergeVideo()
    mv.merge()

if __name__ == '__main__':   
    main()

















