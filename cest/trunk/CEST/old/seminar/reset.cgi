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
    writer << %w(申込番号 名前 ふりがな 郵便番号 住所 会社名 部署名 役職名 電話番号 E-mailアドレス 会員種別 懇親会 請求書の有無 自由記載欄 参加費用).map {|i| NKF.nkf('-s', i)}
  }
}
File.chmod(0666, LFile)
