import sre_parse

# Define a simple regular expression
# pattern = r'ab+c'
# pattern = r'^.[a-z123]*(?:foo(?:bar)|(?:baz))(a|y)$'
# pattern = r'.'

# 从参数中读取正则表达式
import sys
pattern = sys.argv[1] 

# Parse the regular expression
parsed = sre_parse.parse(pattern)

# Print the parsed representation
print(parsed) # example:
# print(parsed.dump())


# 递归处理parsed
def process_parsed(parsed):
    # 如果parsed是一个普通的list
    if isinstance(parsed, list):
        # 遍历parsed中的每一个元素
        results = []
        for item in parsed:
            # 递归处理item
            results.append(process_parsed(item))
        # 去除results中的空字符串
        results = [item for item in results if item != ""]
        return "(re.++ " + " ".join(results) + ")" if len(results) > 1 else results[0] if len(results) == 1 else "(re.none)"
    # 如果OPCODE是SUBPATTERN(存在data成员)
    elif hasattr(parsed, "data"):
        return process_parsed(parsed.data)
    # 如果parsed是一个普通的tuple
    elif isinstance(parsed, tuple):
        OPCODE = parsed[0]
        # 如果OPCODE是AT
        if OPCODE == sre_parse.AT:
            # 返回一个空字符串
            return ""
        # 如果OPCODE是LITERAL
        elif OPCODE == sre_parse.LITERAL:
            return "(str.to_re \"" + chr(parsed[1]) + "\")"
        # 如果OPCODE是RANGE
        elif OPCODE == sre_parse.RANGE:
            return "(re.range \"" + chr(parsed[1][0]) + "\" \"" + chr(parsed[1][1]) + "\")"
        # 如果OPCODE是ANY
        elif OPCODE == sre_parse.ANY:
            return "re.allchar"
        # 如果OPCODE是CATEGORY
        elif OPCODE == sre_parse.CATEGORY:
            # TODO: 根据category内容返回
            # 用英语报错"不支持CATEGORY"
            raise Exception("CATEGORY(like \d, \w, \s, etc.) is not supported")
        # 如果OPCODE是IN
        elif OPCODE == sre_parse.IN:
            # 只有一个元素
            if len(parsed[1]) == 1:
                return process_parsed(parsed[1][0])
            # 多个元素
            else:
                return "(re.union " + " ".join([process_parsed(item) for item in parsed[1]]) + ")" if len(parsed[1]) > 1 else process_parsed(parsed[1][0])
        # 如果OPCODE是BRANCH
        elif OPCODE == sre_parse.BRANCH:
            return "(re.union " + " ".join([process_parsed(item) for item in parsed[1][1]]) + ")" if len(parsed[1][1]) > 1 else process_parsed(parsed[1][1][0])
        # 如果OPCODE是MAX_REPEAT或MIN_REPEAT
        elif OPCODE == sre_parse.MAX_REPEAT or OPCODE == sre_parse.MIN_REPEAT:
            min = parsed[1][0]
            max = parsed[1][1]
            result = process_parsed(parsed[1][2])
            # 如果max是MAXREPEAT
            if max == sre_parse.MAXREPEAT:
                # 如果min是0
                if min == 0:
                    return "(re.* " + result + ")"
                # 如果min是1
                elif min == 1:
                    return "(re.+ " + result + ")"
                # 如果min是其他
                else:
                    return "(re.++ " + " ".join([result] * min) + "(re.* " + result + "))"
            # 如果max不是MAXREPEAT
            else:
                if min < 1 and max - min <= 1:
                    return "(re.opt " + result + ")"
                result_ = "(re.opt " + result + ")"
                return "(re.++ " + " ".join([result] * min) + " ".join([result_] * (max - min)) + ")"
        # 如果OPCODE是SUBPATTERN
        elif OPCODE == sre_parse.SUBPATTERN:
            return process_parsed(parsed[1][3])
        # 其他
        else:
            # 用英语报错"不支持OPCODE"
            raise Exception("OPCODE {} is not supported".format(OPCODE))

print("-"*10, "parsed", "-"*10)
SMT_CONTENT = "(set-logic QF_SLIA) \n\
(set-option :strings-exp true) \n\
(declare-fun v1 () String) \n\
(assert (str.in_re v1 {} )) \n\
(check-sat) \n\
(get-model)".format(process_parsed(parsed))
print(SMT_CONTENT)

# 将SMT_CONTENT写入文件
with open("test.smt2", "w") as f:
    f.write(SMT_CONTENT)

# 使用cvc5求解（./cvc5-Linux --lang=smt2 test.smt2  --produce-models）
import subprocess
result = subprocess.run(["./cvc5-Linux", "--lang=smt2", "test.smt2", "--produce-models"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print("-"*10, "result.stdout", "-"*10)
print(result.stdout.decode("utf-8"))
print("-"*10, "result.stderr", "-"*10)
print(result.stderr.decode("utf-8"))

# # 从result.stdout中提取结果：提取(define-fun v1 () String "[]")中的[]
# import re
# result = re.search(r'\(define-fun v1 \(\) String "(.*)"\)', result.stdout.decode("utf-8"))

# 从result.stdout中提取结果
# result.stdout.decode("utf-8")的内容如下：
# sat
# (
# (define-fun v1 () String "Afoobara")
# )
ans = result.stdout.decode("utf-8")[32:-5].strip()
print("-"*10, "ans", "-"*10)
print(ans)