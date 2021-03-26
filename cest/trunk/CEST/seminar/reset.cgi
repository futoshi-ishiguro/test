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
    writer << %w(受付ID 名前 ふりがな 会社名 部署名 役職名 E-mailアドレス 電話番号 郵便番号 住所 会員種別 懇親会 請求書の有無 自由記載欄 参加費用).map {|i| NKF.nkf('-s', i)}
  }
}
#File.chmod(0666, LFile)
