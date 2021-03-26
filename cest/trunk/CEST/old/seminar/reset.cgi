#!/home/yamamoto/bin/ruby

require 'csv'
require 'nkf'

NFile = 'number'
LFile = 'list.csv'

File.open(NFile, 'w') {|file|
  file.puts(0)
}
File.chmod(0666, NFile)

File.open(LFile, 'w') {|file|
  CSV::Writer.generate(file, ?,, "\r\n") {|writer|
    writer << %w(�����ֹ� ̾�� �դ꤬�� ͹���ֹ� ���� ���̾ ����̾ ��̾ �����ֹ� E-mail���ɥ쥹 ������� ���Ʋ� ������̵ͭ ��ͳ������ ��������).map {|i| NKF.nkf('-s', i)}
  }
}
File.chmod(0666, LFile)
