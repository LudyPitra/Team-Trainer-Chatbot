import gradio as gr
from agent.agent import agent, ctx


async def novamente_chat(message, history):
    try:
        response = await agent.run(message, ctx=ctx)
        return str(response)
    except Exception as e:
        return f"Erro ao processar: {str(e)}"


demo = gr.ChatInterface(
    fn=novamente_chat,
    title="NovaMente Assistant",
    description="Assistente interno de IA para políticas de RH, benefícios, cultura e procedimentos da NovaMente.",
    examples=[
        "Como funciona a nossa política de férias?",
        "Quais são os benefícios de saúde oferecidos?",
        "Onde encontro o código de ética?",
    ],
)

if __name__ == "__main__":
    demo.launch()
