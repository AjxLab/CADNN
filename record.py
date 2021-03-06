#!/usr/bin/env python
import pyaudio, wave
import time, os, threading


class Recording(object):
    def __init__(self):
        ## -----*----- コンストラクタ -----*----- ##
        self._pa = pyaudio.PyAudio()
        # 音声入力の設定
        self.settings = {
            'format': pyaudio.paInt16,
            'channels': 1,
            'rate': 8000,
            'chunk': 1024,
            'past_second': 0.2
        }
        self.stream = self._pa.open(
            format=self.settings['format'],
            channels=self.settings['channels'],
            rate=self.settings['rate'],
            input=True,
            output=False,
            frames_per_buffer=self.settings['chunk']
        )
        # 音声データの格納リスト（past：欠け補完，main：メインの録音）
        self.audio = {'past': [], 'main': []}
        # 録音開始・終了フラグ
        self.record_start = threading.Event()
        self.record_end = threading.Event()
        # 録音ファイル
        self.file = './tmp/voice.wav'

        self.exe()

    def exe(self):
        ## -----*----- 処理実行 -----*----- ##
        # フラグの初期化
        self.is_exit = False
        self.record_start.clear()
        self.record_end.set()

        # 欠け補完部分の録音
        self.past_record(True)

        # サブスレッド起動
        self.thread = threading.Thread(target=self.loop)
        self.thread.start()

    def loop(self):
        ## -----*----- ループ（録音） -----*----- ##
        while not self.is_exit:
            if self.record_start.is_set():
                self.record()
                self.past_record(True)
            else:
                self.past_record(False)

        # 音声録音を行うスレッドを破壊
        del self.thread

    def record(self):
        ## -----*----- 音声録音 -----*----- ##
        # 開始フラグが降りるまで音声データを格納
        while self.record_start.is_set():
            self.audio['main'].append(self.input_audio())
        # ファイル保存
        self.save_audio()

    def past_record(self, init=False):
        ## -----*----- 欠け補完部分の録音 -----*----- ##
        if self.settings['past_second'] == 0:
            return
        if init:
            self.audio['past'] = []
            for i in range(int(self.settings['rate'] / self.settings['chunk'] * self.settings['past_second'])):
                self.audio['past'].append(self.input_audio())
        else:
            self.audio['past'].pop(0)
            self.audio['past'].append(self.input_audio())

    def save_audio(self):
        ## -----*----- 音声データ保存 -----*----- ##
        # 音声ファイルのフォーマット指定
        wav = wave.open(self.file, 'wb')
        wav.setnchannels(self.settings['channels'])
        wav.setsampwidth(self._pa.get_sample_size(self.settings['format']))
        wav.setframerate(self.settings['rate'])

        # 音声データをファイルに書き込み
        wav.writeframes(b''.join(self.audio['main']))
        wav.close()

        # 音声データの初期化
        self.audio = {'past': [], 'main': []}
        self.record_end.set()

    def input_audio(self):
        ## -----*----- 音声入力 -----*----- ##
        return self.stream.read(self.settings['chunk'], exception_on_overflow=False)



if __name__ == '__main__':
    record = Recording()

    context = input('コンテキスト(1 or 2)：')
    save_dir = 'data/context' + context + '/'
    target = input('ターゲット音：')

    os.makedirs(save_dir + target)

    os.system('clear')
    print('*** ENTERを押して録音開始・終了 ***')

    mode = 0  # 0：録音開始，1：録音終了
    cnt = 1

    while True:
        key = input()

        if mode == 0:
            # 録音開始
            print('===== {0} START ==============='.format(cnt))
            record.record_start.set()
            record.record_end.clear()
            mode = 1

        else:
            # 録音終了
            print('===== END ===============')
            record.file = '%s%s/%d.wav' % (save_dir, target, cnt)
            record.record_start.clear()
            while not record.record_end.is_set():
                pass
            mode = 0
            cnt += 1
