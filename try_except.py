# ============================================================
# Python try / except 完整参考
# 包含：基本语法、else / finally、raise、常见内置异常、最佳实践
# ============================================================


# ============================================================
# 一、基本 try - except
# ============================================================
# 语法：
#   try:
#       可能出错的代码
#   except 异常类型:
#       捕获到该异常时执行

# --- 1.1 捕获指定异常 ---
try:
    result = 10 / 0
except ZeroDivisionError:
    print("除数不能为 0")

# --- 1.2 捕获多种异常（元组）---
try:
    num = int("abc")
except (ValueError, TypeError):
    print("无法转换为整数")

# --- 1.3 捕获所有异常（不推荐！见第八节）---
try:
    x = open("不存在的文件.txt")
except Exception:          # Exception 是大多数异常的基类
    print("出问题了")


# ============================================================
# 二、获取异常对象： as
# ============================================================
# 使用 as 把异常实例绑定到变量，可以打印/传递

try:
    10 / 0
except ZeroDivisionError as e:
    print(f"异常类型：{type(e).__name__}")     # ZeroDivisionError
    print(f"异常信息：{e}")                     # division by zero


# ============================================================
# 三、try - except - else
# ============================================================
# else 子句：只有 try 块**没有抛出异常**时才会执行
# 用途：把"可能出错的代码"和"成功后才该跑的代码"分开，更清晰

try:
    f = open("try_except.py", "r", encoding="utf-8")
except FileNotFoundError:
    print("文件不存在")
else:
    content = f.read()
    f.close()                       # 成功打开才需要关闭
    print(f"读取成功，共 {len(content)} 字符")


# ============================================================
# 四、try - except - finally
# ============================================================
# finally 子句：**无论是否发生异常都会执行**
# 典型用途：资源释放（文件关闭、锁释放、连接关闭）

# --- 4.1 基本用法 ---
f = None
try:
    f = open("try_except.py", "r", encoding="utf-8")
    content = f.read()
except Exception as e:
    print(f"读取失败：{e}")
finally:
    if f:
        f.close()    # 无论成功还是失败，都确保文件关闭

# --- 4.2 finally 中的 return / raise ---
# 如果 finally 里有 return / raise，它会覆盖 try/except 里的 return
def demo_finally():
    try:
        return "try 中的返回"
    finally:
        return "finally 中的返回"    # 最终返回这个！

print(demo_finally())   # 输出：finally 中的返回


# ============================================================
# 五、完整结构：try - except - else - finally
# ============================================================
# 顺序固定：try → except → else → finally（else 和 finally 可选）
# 执行流程：
#   无异常：try → else → finally
#   有异常：try(中断) → except → finally

# 演示执行流程（避免 input() 阻塞，直接用 try-except-else-finally）
def calc_square(text):
    try:
        num = int(text)                   # 传入非数字会触发 ValueError
    except ValueError as e:
        print(f"输入有误：{e}")
        return None
    else:
        square = num ** 2
        print(f"平方是 {square}")
        return square
    finally:
        print("程序结束")

calc_square("5")       # else 和 finally 都会执行
calc_square("abc")     # except 和 finally 都会执行


# ============================================================
# 六、主动抛出异常：raise
# ============================================================

# --- 6.1 抛出内置异常 ---
def set_age(age):
    if age < 0:
        raise ValueError("年龄不能为负数")
    return age

# set_age(-5)   # 运行时会抛出 ValueError: 年龄不能为负数

# --- 6.2 重新抛出（在 except 中用 bare raise）---
# 如果想在 except 中记录日志后继续向上抛
def risky_divide(a, b):
    try:
        return a / b
    except ZeroDivisionError:
        print("记录了一条错误日志")
        raise              # 裸 raise：原样重新抛出当前异常

# risky_divide(10, 0)   # 运行时会向上抛出 ZeroDivisionError

# --- 6.3 异常链：raise NewError(...) from e ---
# 保留原始异常的同时，抛出更高层的业务异常
class DataLoadError(Exception):
    pass

def load_data():
    try:
        # 模拟底层异常
        int("bad data")
    except ValueError as e:
        raise DataLoadError("数据加载失败") from e

# load_data()
# 输出类似：
#   DataLoadError: 数据加载失败
#   The above exception was the direct cause of the following exception:
#   ValueError: invalid literal for int() with base 10: 'bad data'


# ============================================================
# 七、自定义异常
# ============================================================
# 继承 Exception（或其子类）即可

class LoginError(Exception):
    """登录失败的自定义异常"""
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code

class NetworkError(LoginError):
    """网络原因导致的登录失败"""
    pass

class CaptchaError(LoginError):
    """验证码原因导致的登录失败"""
    pass

def login(username, password):
    if not username or not password:
        raise LoginError("用户名和密码不能为空", code=1001)
    if password != "secret":
        raise LoginError("密码错误", code=1002)
    return True

# 使用
try:
    login("alice", "")
except LoginError as e:
    print(f"登录失败 [{e.code}]：{e}")


# ============================================================
# 八、常见内置异常一览
# ============================================================
# 继承链（简化）：
#   BaseException
#   ├── SystemExit          sys.exit() 抛出
#   ├── KeyboardInterrupt   Ctrl+C
#   └── Exception
#       ├── ArithmeticError
#       │   └── ZeroDivisionError    10/0
#       ├── AssertionError           assert False
#       ├── AttributeError           obj.不存在的属性
#       ├── EOFError                 input() 读到 EOF
#       ├── ImportError
#       │   └── ModuleNotFoundError  import 不存在的模块
#       ├── IndexError               列表索引越界
#       ├── KeyError                 字典 key 不存在
#       ├── MemoryError              内存不足
#       ├── NameError                使用未定义变量
#       │   └── UnboundLocalError
#       ├── OSError  (IOError)
#       │   ├── FileNotFoundError
#       │   ├── PermissionError
#       │   └── TimeoutError
#       ├── OverflowError            数值溢出
#       ├── RecursionError           递归过深
#       ├── RuntimeError
#       │   └── NotImplementedError  未实现的抽象方法
#       ├── StopIteration            迭代器耗尽
#       ├── SyntaxError
#       │   └── IndentationError     缩进错误
#       ├── TypeError                类型不匹配
#       ├── ValueError               值不合法（类型对但值不对）
#       │   └── UnicodeError        编码错误
#       └── Warning (Warning 是 Exception 的子类)


# --- 各异常触发示例 ---
try:        10 / 0                # ZeroDivisionError
except Exception as e: print(type(e).__name__)

try:        [] + 1                # TypeError
except Exception as e: print(type(e).__name__)

try:        [1, 2, 3][10]         # IndexError
except Exception as e: print(type(e).__name__)

try:        {"a": 1}["b"]         # KeyError
except Exception as e: print(type(e).__name__)

try:        int("abc")            # ValueError
except Exception as e: print(type(e).__name__)

try:        open("nofile.txt")    # FileNotFoundError
except Exception as e: print(type(e).__name__)

try:        print(undefined_var)  # NameError
except Exception as e: print(type(e).__name__)

try:        import nonexistent    # ModuleNotFoundError
except Exception as e: print(type(e).__name__)


# ============================================================
# 九、Python 3.11+ 的 ExceptionGroup
# ============================================================
# 一次性捕获多种异常（多异常并发场景，如 asyncio）
# 注意：需要 Python 3.11+，3.10 及以下版本不支持

# try:
#     raise ExceptionGroup("多任务失败", [
#         ValueError("任务A失败"),
#         KeyError("任务B失败"),
#     ])
# except* ValueError as e:
#     print(f"捕获到 ValueError：{e.exceptions}")
# except* KeyError as e:
#     print(f"捕获到 KeyError：{e.exceptions}")


# ============================================================
# 十、上下文管理器 with —— try / finally 的语法糖
# ============================================================
# with 自动帮你做了 try-finally 的资源清理
# 下面两段代码等价：

# --- 写法 1：显式 try-finally ---
f = open("try_except.py")
try:
    content = f.read()
finally:
    f.close()

# --- 写法 2：with（推荐）---
with open("try_except.py") as f:
    content = f.read()
# 离开 with 块后自动调用 f.close()

# SeleniumBase 中你已经在用这个模式：
# with SB(**SB_KWARGS) as sb:
#     ...操作...
# 离开 with 块后浏览器自动关闭


# ============================================================
# 十一、最佳实践 & 反模式
# ============================================================

# --- ✅ 应该做的 ---
# 1) 捕获具体的异常类型，而不是 except: 或 except Exception:
#    try:
#        int(s)
#    except ValueError:              # ✅ 精准
#        pass

# 2) 在 except 中记录原始异常（logger.exception 自动带 traceback）
#    logger.exception("操作失败")
#    # 或：logger.error(f"操作失败: {e}", exc_info=True)

# 3) 用 else 分离成功/失败路径
#    try:        data = parse(raw)
#    except ParseError:  handle_parse_error()
#    else:       save(data)          # 只有解析成功才保存

# 4) 用 with 管理资源（文件、连接、锁）

# --- ❌ 不该做的 ---
# 1) 空 except（会吞掉 KeyboardInterrupt / SystemExit，用户无法 Ctrl+C）
#    try:        time.sleep(100)
#    except:      pass                # ❌

# 2) 过度捕获，隐藏 bug
#    try:        x = obj.attribty     # 拼错了属性名
#    except Exception:  pass          # ❌ 把 AttributeError 也吞了

# 3) 在 finally 中 return（会覆盖 try/except 的 return，易引发困惑）

# 4) 用异常做正常流程控制（性能差 + 可读性差）

# 5) raise 时不保留原始异常
#    raise MyError("出错了")          # ❌ 原始 ValueError 丢失
#    raise MyError("出错了") from e   # ✅ 保留原始异常


# ============================================================
# 十二、速查：何时用哪种结构
# ============================================================
#
# 场景                                  推荐结构
# ──────────────────────────────────    ─────────────────────────
# 可能出错，出错就处理                  try - except
# 出错做 A，不出错做 B                   try - except - else
# 必须释放资源（文件/连接/锁）           try - finally 或 with
# 既要处理又要释放资源                   try - except - finally
# 出错后要把异常包装上抛                 raise NewError(...) from e
# 主动触发异常                           raise ValueError("msg")
# 定义业务特有的错误类型                 class MyError(Exception)
