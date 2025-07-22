import logging
import requests
import json
import re
from flask import current_app
from time import sleep

logger = logging.getLogger(__name__)

class AIService:
    def __init__(self):
        self.base_url = "https://api.groq.com/openai/v1/chat/completions"
        
    def _get_api_key(self):
        """Get Groq API key from Flask config"""
        api_key = current_app.config.get('GROQ_API_KEY')
        if not api_key:
            logger.error("Groq API key not found in configuration")
        return api_key
    
    def generate_questions(self, job_description):
        """Generate interview questions using Groq API"""
        api_key = self._get_api_key()
        if not api_key:
            logger.warning("Using fallback questions due to missing API key")
            return self._fallback_questions(job_description)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Based on the following job description, generate exactly 5 relevant interview questions that would help screen candidates effectively:

Job Description: {job_description}

Please generate questions that assess:
1. Technical skills relevant to the role
2. Communication abilities
3. Problem-solving skills
4. Experience and background
5. Cultural fit

Return only the questions, one per line, without numbering or bullet points."""

        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert HR interviewer. Generate clear, relevant interview questions based on job descriptions."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7,
            "max_tokens": 500
        }
        
        try:
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            generated_text = result['choices'][0]['message']['content']
            questions = self._parse_questions(generated_text)
            
            if len(questions) >= 3:
                logger.info(f"Generated {len(questions)} questions for job description")
                return questions[:5]
            else:
                logger.warning("Generated questions were insufficient, using fallback")
                return self._fallback_questions(job_description)
                
        except requests.exceptions.Timeout:
            logger.error("Groq API timeout, using fallback questions")
            return self._fallback_questions(job_description)
        
        except requests.exceptions.HTTPError as e:
            logger.error(f"Groq API HTTP error: {e}")
            return self._fallback_questions(job_description)
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Groq API request failed: {e}")
            return self._fallback_questions(job_description)
    
    def _parse_questions(self, text):
        """Parse questions from generated text"""
        lines = text.strip().split('\n')
        questions = []
        
        for line in lines:
            line = line.strip()
            line = re.sub(r'^[\d\.\-\*\•\s]+', '', line)
            
            if line and ('?' in line or line.endswith('.')) and len(line) > 10:
                if not line.endswith('?'):
                    line = line.rstrip('.') + '?'
                questions.append(line)
        
        if not questions:
            potential_questions = text.split('?')
            for q in potential_questions:
                q = q.strip()
                q = re.sub(r'^[\d\.\-\*\•\s]+', '', q)
                if q and len(q) > 10:
                    questions.append(q + '?')
        
        return questions
    
    def _fallback_questions(self, job_description):
        """Generate fallback questions based on job description analysis"""
        logger.info("Generating fallback questions")
        job_desc_lower = job_description.lower()
        questions = []
        
        if any(keyword in job_desc_lower for keyword in ['java', 'python', 'javascript', 'react', 'node', 'angular', 'vue']):
            questions.append("Can you walk me through your experience with the programming languages and frameworks mentioned in this role?")
        
        if any(keyword in job_desc_lower for keyword in ['database', 'sql', 'mysql', 'postgresql', 'mongodb']):
            questions.append("How do you approach database design and what experience do you have with database optimization?")
        
        if any(keyword in job_desc_lower for keyword in ['api', 'rest', 'microservices', 'web services']):
            questions.append("Describe your experience with API development and integration. Can you give an example?")
        
        if any(keyword in job_desc_lower for keyword in ['cloud', 'aws', 'azure', 'gcp', 'docker', 'kubernetes']):
            questions.append("What is your experience with cloud platforms and containerization technologies?")
        
        if any(keyword in job_desc_lower for keyword in ['agile', 'scrum', 'team', 'collaboration']):
            questions.append("How do you handle working in an agile environment and what's your approach to team collaboration?")
        
        generic_questions = [
            "What interests you most about this position and why do you want to work here?",
            "How do you stay current with new technologies and industry trends?",
            "Describe a situation where you had to quickly learn a new technology or tool.",
            "What are your long-term career goals and how does this role fit into them?",
            "Tell me about a time you received feedback on your work and how you handled it."
        ]
        
        for generic_q in generic_questions:
            if len(questions) >= 5:
                break
            if generic_q not in questions:
                questions.append(generic_q)
        
        logger.info(f"Generated {len(questions)} fallback questions")
        return questions[:5]
    
    def analyze_response(self, transcript, question_text=""):
        """Analyze candidate response using Groq API"""
        api_key = self._get_api_key()
        if not api_key:
            logger.warning("Using fallback analysis due to missing API key")
            return self._fallback_analysis(transcript, question_text)
        
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        prompt = f"""Analyze the following candidate's interview response and provide scoring in JSON format:

Question: {question_text}
Candidate Response: {transcript}

Evaluate the response for:
1. Communication Score (0-100): Clarity, articulation, structure
2. Technical Score (0-100): Technical knowledge, relevant experience, problem-solving
3. Overall Recommendation: "Select", "Consider", or "Reject"
4. Reasoning: 1-2 sentences explaining the assessment

Return only a JSON object with these fields, no additional text:
{{
    "communication_score": <number>,
    "technical_score": <number>,
    "recommendation": "<Select/Consider/Reject>",
    "reasoning": "<brief explanation>"
}}"""

        payload = {
            "model": "llama3-8b-8192",
            "messages": [
                {
                    "role": "system",
                    "content": "You are an expert interview evaluator. Provide structured feedback in JSON format with no additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.3,
            "max_tokens": 300
        }
        
        for attempt in range(3):
            try:
                response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
                response.raise_for_status()
                
                result = response.json()
                generated_text = result['choices'][0]['message']['content']
                
                try:
                    json_match = re.search(r'\{.*?\}', generated_text, re.DOTALL)
                    if json_match:
                        json_str = json_match.group(0)
                        analysis_result = json.loads(json_str)
                        
                        required_fields = ['communication_score', 'technical_score', 'recommendation', 'reasoning']
                        if all(field in analysis_result for field in required_fields):
                            analysis_result['communication_score'] = min(100, max(0, int(analysis_result['communication_score'])))
                            analysis_result['technical_score'] = min(100, max(0, int(analysis_result['technical_score'])))
                            logger.info(f"Analysis result: {analysis_result}")
                            return analysis_result
                    logger.warning(f"No valid JSON found in analysis response: {generated_text}")
                    sleep(2 ** attempt)
                    continue
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON from analysis response: {generated_text}")
                    sleep(2 ** attempt)
                    continue
                    
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 429:
                    logger.warning(f"Rate limit hit, retrying ({attempt + 1}/3)")
                    sleep(2 ** attempt)
                    continue
                logger.error(f"Groq API HTTP error: {e}")
                return self._fallback_analysis(transcript, question_text)
            
            except requests.exceptions.Timeout:
                logger.error("Groq API timeout, using fallback analysis")
                return self._fallback_analysis(transcript, question_text)
            
            except requests.exceptions.RequestException as e:
                logger.error(f"Groq API request failed: {e}")
                return self._fallback_analysis(transcript, question_text)
        
        logger.error("Max retries reached for Groq API, using fallback")
        return self._fallback_analysis(transcript, question_text)
    
    def _fallback_analysis(self, transcript, question_text=""):
        """Rule-based analysis as fallback"""
        logger.info("Performing fallback analysis")
        word_count = len(transcript.split())
        sentence_count = len([s for s in transcript.split('.') if s.strip()])
        
        communication_score = 50
        technical_score = 50
        
        if word_count < 20:
            communication_score = 30
        elif word_count < 50:
            communication_score = 50
        elif word_count < 100:
            communication_score = 70
        else:
            communication_score = 80
        
        good_indicators = ['because', 'therefore', 'for example', 'specifically', 'in my experience']
        if any(indicator in transcript.lower() for indicator in good_indicators):
            communication_score = min(100, communication_score + 10)
        
        technical_keywords = [
            'algorithm', 'database', 'framework', 'api', 'code', 'programming',
            'system', 'architecture', 'performance', 'optimization', 'testing',
            'java', 'python', 'javascript', 'react', 'node', 'sql', 'git'
        ]
        
        tech_mentions = sum(1 for keyword in technical_keywords if keyword.lower() in transcript.lower())
        if tech_mentions > 0:
            technical_score = min(100, 50 + tech_mentions * 10)
        
        experience_indicators = ['worked with', 'implemented', 'developed', 'designed', 'built', 'created']
        if any(indicator in transcript.lower() for indicator in experience_indicators):
            technical_score = min(100, technical_score + 10)
        
        avg_score = (communication_score + technical_score) / 2
        if avg_score >= 70:
            recommendation = "Select"
        elif avg_score >= 50:
            recommendation = "Consider"
        else:
            recommendation = "Reject"
        
        reasoning = f"Response length: {word_count} words. Found {tech_mentions} technical terms. Average score: {avg_score:.1f}/100."
        logger.info(f"Fallback analysis result: {reasoning}")
        
        return {
            "communication_score": communication_score,
            "technical_score": technical_score,
            "recommendation": recommendation,
            "reasoning": reasoning
        }