#!/usr/local/bin/ruby --
# #! /home/yamamoto/app/bin/ruby --

require 'csv'
require 'nkf'

NFile  = 'number'
NFile2 = 'number2'
##NFile3 = 'number3'
LFile  = 'list.csv'

File.open(NFile, 'w') {|file|
  file.puts('0')
}
File.open(NFile2, 'w') {|file|
  file.puts('0')
}
#File.open(NFile3, 'w') {|file|
#  file.puts('0')
#}
#File.chmod(0666, NFile)
#File.chmod(0666, NFile2)
#File.chmod(0666, NFile3)

File.open(LFile, 'w') {|file|
  CSV::Writer.generate(file, ?,, "\r\n") {|writer|
    writer << %w(����ID ̾�� �դ꤬�� ���̾ ����̾ ��̾ E-mail���ɥ쥹 �����ֹ� ͹���ֹ� ���� ������� ���Ʋ� ������̵ͭ ��ͳ������ ��������).map {|i| NKF.nkf('-s', i)}
  }
}
#File.chmod(0666, LFile)
