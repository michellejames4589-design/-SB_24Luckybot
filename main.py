import os
import ast
import operator as op
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

# --- Safe Expression Evaluator ---
OPERATORS = {
    ast.Add: op.add,
    ast.Sub: op.sub,
    ast.Mult: op.mul,
    ast.Div: op.truediv,
    ast.Pow: op.pow,
    ast.Mod: op.mod,
    ast.USub: op.neg,
    ast.UAdd: op.pos,
}

class SafeEval(ast.NodeVisitor):
    def visit(self, node):
        if isinstance(node, ast.Expression):
            return self.visit(node.body)
        elif isinstance(node, ast.BinOp):
            left = self.visit(node.left)
            right = self.visit(node.right)
            oper = OPERATORS.get(type(node.op))
            if oper is None:
                raise ValueError("Unsupported operator")
            return oper(left, right)
        elif isinstance(node, ast.UnaryOp):
            operand = self.visit(node.operand)
            oper = OPERATORS.get(type(node.op))
            if oper is None:
                raise ValueError("Unsupported unary operator")
            return oper(operand)
        elif isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise ValueError("Unsupported constant")
        else:
            raise ValueError("Unsupported expression")

def safe_eval(expression: str):
    """Safely evaluate a mathematical expression string."""
    try:
        tree = ast.parse(expression, mode='eval')
        return SafeEval().visit(tree)
    except Exception:
        return None

# --- Bot Handlers ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🧮 Simple Calculator Bot\n\n"
        "Send me a math expression like:\n"
        "• 2+2\n"
        "• 10*5/2\n"
        "• (3+4)*2\n\n"
        "I support +, -, *, /, **, %."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Send any arithmetic expression and I'll calculate it.\n\n"
        "Examples:\n"
        "• 7+8\n"
        "• 100/4\n"
        "• 2**10"
    )

async def calculate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    result = safe_eval(text)
    if result is not None:
        await update.message.reply_text(f"= {result}")
    else:
        await update.message.reply_text("❌ Could not evaluate that expression.")

# --- Main ---
if __name__ == "__main__":
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable not set")

    app = ApplicationBuilder().token(token).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, calculate))

    print("Bot is starting...")
    app.run_polling()
