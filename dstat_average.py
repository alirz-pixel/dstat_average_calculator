import argparse
import re
import json


parser = argparse.ArgumentParser(description="'dstat' average calculator", add_help=False)
parser.add_argument("filename", type=argparse.FileType('r'), help="path to the dstat output file")
parser.add_argument("-h", "--human-readable", action='store_true', help="print sizes like 1K 234M 2G etc.")
parser.add_argument("--help", required=False, action='store_true', help="display this help and exit")


def get_num(bytes_str):
    mul_val = 1
    if "k" in bytes_str:
        mul_val = 1000
    elif "M" in bytes_str:
        mul_val = 1000 * 1000
    return int(re.sub(r'[^0-9]', '', bytes_str)) * mul_val



def get_split_element(line):
    bytes = []
    tmp = line.strip().split("|")
    for e in tmp:
        bytes.extend(e.split())

    ret = []
    for byte in bytes:
        ret.append(get_num(byte))
    return ret


def byte_transform(bytes, bsize=1000):
    to = ["bytes", "KB", "MB", "GB", "TB", "PB"]
    cnt = 0
    while (bytes >= bsize):
        bytes /= bsize
        cnt += 1
    return str(round(bytes, 2)) + " " + to[cnt]


def get_average(file, human_readable):
    start_cal = False
    header_list = []
    
    cnt = 0
    total_list = []
    for line in file.readlines():
        if start_cal == False:
            if "read" in line:
                start_cal = True
                header = line.strip().split("|")
                for e in header:
                    header_list.extend(e.split())
                    total_list = [0] * len(header_list)
            continue

        element_list = get_split_element(line)
        cnt += 1
        total_list = [x + y for x, y in zip(total_list, element_list)]

    if cnt == 0:
        print("error: 측정된 dstat이 없음")
        exit()

    ret = {}
    except_headers = ["usr", "sys", "idl", "wai", "stl"]
    for i in range(len(header_list)):
        if header_list[i] in except_headers:
            continue

        if human_readable:
            ret[header_list[i]] = byte_transform(total_list[i] / cnt)
        else:
            ret[header_list[i]] = str(total_list[i] / cnt) + " bytes" 

    return ret


def get_average_csv(file, human_readable):
    start_cal = False
    header_list = []
    line_list = []
    header_top_line_num = -1
    
    cnt = 0
    total_list = []
    for line in file.readlines():
        if start_cal == False:
            line_list.append(line)
            header_top_line_num += 1
            if "read" in line:
                start_cal = True
                header_list = line.replace('"', "").strip().split(",")
                total_list = [0] * len(header_list)
            continue

        element_list = list(map(float, line.split(",")))
        cnt += 1
        total_list = [x + y for x, y in zip(total_list, element_list)]

    if cnt == 0:
        print("error: 측정된 dstat이 없음")
        exit()

    header_top_list = line_list[header_top_line_num - 1].strip().replace('"', '').split(",")
    
    except_headers = ["total cpu usage", "procs", "tcp sockets"]
    cur_header_top = ""
    ret = {}
    for i in range(len(header_list)):
        if header_top_list[i] != "":
            cur_header_top = header_top_list[i]
            if ret.get(cur_header_top, None) is None:
                ret[cur_header_top] = {}

        div_result = round(total_list[i] / cnt, 2)
        if human_readable:
            ret[cur_header_top][header_list[i]] = div_result if cur_header_top in except_headers else byte_transform(div_result)
        else:
            ret[cur_header_top][header_list[i]] = str(div_result) + ("" if cur_header_top in except_headers else " bytes")

    return ret



if __name__ == "__main__":
    args = parser.parse_args()
    if args.help:
        parser.print_help()
        exit()

    ret = {}
    if "csv" in args.filename.name:
        ret = get_average_csv(args.filename, args.human_readable)
    else:
        ret = get_average(args.filename, args.human_readable)

    print(json.dumps(ret, indent=2, ensure_ascii=False))
    # try:
    # except Exception as e:
    #     print(e)
    #     print("dstat 결과 파일이 깨졌거나 읽을 수 없습니다.")
