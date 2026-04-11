import os
from openai import OpenAI

class OpenAIService:
	def __init__(self):
		self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

	async def handle(self, request):
		# This is a placeholder. You may want to adapt this to your needs.
		messages = getattr(request, "messages", None)
		if not messages:
			messages = [{"role": "user", "content": request.message}]
		response = self.client.chat.completions.create(
			model="gpt-4o-mini",
			messages=messages
		)
		answer = response.choices[0].message.content or ""
		return {"answer": answer}
