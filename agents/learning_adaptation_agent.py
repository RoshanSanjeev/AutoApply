"""
Learning and Adaptation Agent - Continuously learns from application outcomes
"""
import os
import json
import time
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict, Counter
import requests

from utils.logger import setup_logger


class LearningAdaptationAgent:
    """Agent that learns from application outcomes and adapts strategy"""
    
    def __init__(self):
        self.logger = setup_logger("learning_adaptation")
        
        # Load historical data
        self.application_history = self._load_application_history()
        self.performance_data = self._load_performance_data()
        self.learning_models = self._load_learning_models()
        
        # Learning parameters
        self.learning_rate = 0.1
        self.min_samples_for_learning = 10
        self.confidence_threshold = 0.7
        
        # NVIDIA API for advanced analysis
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.base_url = "https://integrate.api.nvidia.com/v1"
        
    def _load_application_history(self) -> List[Dict[str, Any]]:
        """Load historical application data"""
        history_file = "data/application_history.json"
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load application history: {e}")
        
        return []
    
    def _load_performance_data(self) -> Dict[str, Any]:
        """Load performance tracking data"""
        perf_file = "data/performance_data.json"
        
        if os.path.exists(perf_file):
            try:
                with open(perf_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load performance data: {e}")
        
        return {
            "response_rates": {
                "by_company_size": {},
                "by_industry": {},
                "by_role_type": {},
                "by_location": {},
                "by_application_time": {},
                "by_skills_mentioned": {}
            },
            "success_patterns": {
                "best_performing_keywords": [],
                "optimal_application_timing": [],
                "successful_resume_formats": [],
                "effective_cover_letter_styles": []
            },
            "learning_insights": {
                "skill_demand_trends": {},
                "company_preference_patterns": {},
                "market_timing_insights": {},
                "personalization_effectiveness": {}
            }
        }
    
    def _load_learning_models(self) -> Dict[str, Any]:
        """Load trained learning models and patterns"""
        models_file = "data/learning_models.json"
        
        if os.path.exists(models_file):
            try:
                with open(models_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                self.logger.warning(f"Could not load learning models: {e}")
        
        return {
            "response_prediction_model": {
                "weights": {},
                "features": [],
                "accuracy": 0.0,
                "last_trained": None
            },
            "skill_recommendation_model": {
                "skill_scores": {},
                "trending_skills": [],
                "last_updated": None
            },
            "timing_optimization_model": {
                "best_times": {},
                "best_days": {},
                "seasonal_patterns": {}
            }
        }
    
    def learn_from_application_outcome(self, application_data: Dict[str, Any], outcome: Dict[str, Any]):
        """Learn from a single application outcome"""
        self.logger.info(f"Learning from application to {application_data.get('company', 'Unknown')}")
        
        # Record the outcome
        learning_record = {
            "application_id": application_data.get('application_id', ''),
            "timestamp": datetime.now().isoformat(),
            "company": application_data.get('company', ''),
            "position": application_data.get('position', ''),
            "skills_required": application_data.get('required_skills', []),
            "location": application_data.get('location', ''),
            "salary_range": application_data.get('salary_range', ''),
            "application_method": application_data.get('application_method', 'manual'),
            "resume_customization_score": application_data.get('customization_score', 0),
            "cover_letter_personalization": application_data.get('personalization_score', 0),
            
            # Outcome data
            "response_received": outcome.get('response_received', False),
            "response_time_hours": outcome.get('response_time_hours', 0),
            "response_type": outcome.get('response_type', ''),  # rejection, interview, request_info
            "interview_scheduled": outcome.get('interview_scheduled', False),
            "offer_received": outcome.get('offer_received', False),
            "rejection_reason": outcome.get('rejection_reason', ''),
            "feedback_received": outcome.get('feedback_received', ''),
        }
        
        # Add to history
        self.application_history.append(learning_record)
        
        # Update performance data
        self._update_performance_metrics(learning_record)
        
        # Trigger learning updates
        self._update_response_prediction_model()
        self._update_skill_recommendations()
        self._update_timing_optimization()
        
        # Generate insights with AI
        self._generate_ai_insights(learning_record)
        
        # Save updated data
        self._save_learning_data()
        
        self.logger.info("Learning update completed")
    
    def _update_performance_metrics(self, record: Dict[str, Any]):
        """Update performance tracking metrics"""
        
        # Update response rates by various factors
        factors = {
            "by_company_size": self._get_company_size(record['company']),
            "by_industry": self._get_industry(record['company']),
            "by_role_type": self._classify_role_type(record['position']),
            "by_location": record['location'],
        }
        
        for factor_type, factor_value in factors.items():
            if factor_value:
                if factor_value not in self.performance_data["response_rates"][factor_type]:
                    self.performance_data["response_rates"][factor_type][factor_value] = {
                        "total_applications": 0,
                        "responses_received": 0,
                        "interviews_scheduled": 0,
                        "offers_received": 0
                    }
                
                metrics = self.performance_data["response_rates"][factor_type][factor_value]
                metrics["total_applications"] += 1
                
                if record["response_received"]:
                    metrics["responses_received"] += 1
                if record["interview_scheduled"]:
                    metrics["interviews_scheduled"] += 1
                if record["offer_received"]:
                    metrics["offers_received"] += 1
        
        # Update skills performance
        for skill in record.get("skills_required", []):
            if skill not in self.performance_data["response_rates"]["by_skills_mentioned"]:
                self.performance_data["response_rates"]["by_skills_mentioned"][skill] = {
                    "total_applications": 0,
                    "responses_received": 0
                }
            
            skill_metrics = self.performance_data["response_rates"]["by_skills_mentioned"][skill]
            skill_metrics["total_applications"] += 1
            if record["response_received"]:
                skill_metrics["responses_received"] += 1
    
    def _update_response_prediction_model(self):
        """Update the model that predicts application success"""
        if len(self.application_history) < self.min_samples_for_learning:
            return
        
        # Prepare training data
        features = []
        labels = []
        
        for record in self.application_history[-100:]:  # Use last 100 applications
            feature_vector = self._extract_features(record)
            label = 1 if record["response_received"] else 0
            
            features.append(feature_vector)
            labels.append(label)
        
        # Simple learning algorithm (can be enhanced with proper ML)
        feature_weights = {}
        feature_names = [
            "resume_customization_score", "cover_letter_personalization",
            "company_size_score", "skills_match_score", "timing_score"
        ]
        
        for i, feature_name in enumerate(feature_names):
            # Calculate correlation between feature and success
            feature_values = [f[i] for f in features]
            correlation = self._calculate_correlation(feature_values, labels)
            feature_weights[feature_name] = correlation
        
        # Update model
        self.learning_models["response_prediction_model"]["weights"] = feature_weights
        self.learning_models["response_prediction_model"]["features"] = feature_names
        self.learning_models["response_prediction_model"]["last_trained"] = datetime.now().isoformat()
        
        # Calculate model accuracy
        accuracy = self._calculate_model_accuracy(features, labels, feature_weights)
        self.learning_models["response_prediction_model"]["accuracy"] = accuracy
        
        self.logger.info(f"Response prediction model updated. Accuracy: {accuracy:.2f}")
    
    def _extract_features(self, record: Dict[str, Any]) -> List[float]:
        """Extract numerical features from application record"""
        features = [
            record.get("resume_customization_score", 0),
            record.get("cover_letter_personalization", 0),
            self._get_company_size_score(record["company"]),
            self._calculate_skills_match_score(record.get("skills_required", [])),
            self._get_timing_score(record["timestamp"])
        ]
        return features
    
    def _calculate_correlation(self, x: List[float], y: List[int]) -> float:
        """Calculate simple correlation coefficient"""
        if len(x) != len(y) or len(x) < 2:
            return 0.0
        
        x_mean = sum(x) / len(x)
        y_mean = sum(y) / len(y)
        
        numerator = sum((x[i] - x_mean) * (y[i] - y_mean) for i in range(len(x)))
        x_var = sum((x[i] - x_mean) ** 2 for i in range(len(x)))
        y_var = sum((y[i] - y_mean) ** 2 for i in range(len(y)))
        
        denominator = (x_var * y_var) ** 0.5
        
        return numerator / denominator if denominator != 0 else 0.0
    
    def _update_skill_recommendations(self):
        """Update skill recommendations based on market trends"""
        if len(self.application_history) < 5:
            return
        
        # Analyze skill performance
        skill_performance = defaultdict(lambda: {"total": 0, "success": 0})
        
        for record in self.application_history[-50:]:  # Recent applications
            for skill in record.get("skills_required", []):
                skill_performance[skill]["total"] += 1
                if record["response_received"]:
                    skill_performance[skill]["success"] += 1
        
        # Calculate skill scores
        skill_scores = {}
        for skill, stats in skill_performance.items():
            if stats["total"] >= 3:  # Minimum sample size
                score = stats["success"] / stats["total"]
                skill_scores[skill] = score
        
        # Update model
        self.learning_models["skill_recommendation_model"]["skill_scores"] = skill_scores
        self.learning_models["skill_recommendation_model"]["last_updated"] = datetime.now().isoformat()
        
        # Identify trending skills
        trending_skills = sorted(skill_scores.items(), key=lambda x: x[1], reverse=True)[:10]
        self.learning_models["skill_recommendation_model"]["trending_skills"] = [
            {"skill": skill, "score": score} for skill, score in trending_skills
        ]
    
    def _update_timing_optimization(self):
        """Update optimal timing recommendations"""
        if len(self.application_history) < 10:
            return
        
        # Analyze timing patterns
        time_performance = defaultdict(lambda: {"total": 0, "success": 0})
        day_performance = defaultdict(lambda: {"total": 0, "success": 0})
        
        for record in self.application_history:
            timestamp = datetime.fromisoformat(record["timestamp"])
            hour = timestamp.hour
            day = timestamp.strftime("%A")
            
            time_performance[hour]["total"] += 1
            day_performance[day]["total"] += 1
            
            if record["response_received"]:
                time_performance[hour]["success"] += 1
                day_performance[day]["success"] += 1
        
        # Calculate best times
        best_times = {}
        for hour, stats in time_performance.items():
            if stats["total"] >= 2:
                rate = stats["success"] / stats["total"]
                best_times[str(hour)] = rate
        
        best_days = {}
        for day, stats in day_performance.items():
            if stats["total"] >= 2:
                rate = stats["success"] / stats["total"]
                best_days[day] = rate
        
        # Update model
        self.learning_models["timing_optimization_model"]["best_times"] = best_times
        self.learning_models["timing_optimization_model"]["best_days"] = best_days
    
    def _generate_ai_insights(self, record: Dict[str, Any]):
        """Generate insights using NVIDIA AI"""
        if not self.api_key:
            return
        
        try:
            # Prepare data for AI analysis
            recent_history = self.application_history[-20:]  # Last 20 applications
            
            analysis_prompt = f"""
            Analyze this job application data and provide strategic insights:
            
            Latest Application:
            Company: {record['company']}
            Position: {record['position']}
            Skills Required: {record.get('skills_required', [])}
            Outcome: {'Success' if record['response_received'] else 'No response'}
            
            Recent Application Patterns:
            {json.dumps(recent_history, indent=2)}
            
            Provide insights on:
            1. What factors correlate with successful applications
            2. Skills that are trending in the market
            3. Timing patterns for optimal applications
            4. Recommendations for improving success rate
            5. Market trends and opportunities
            
            Return analysis as structured JSON with actionable recommendations.
            """
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "nvidia/llama-3.1-nemotron-70b-instruct",
                "messages": [
                    {"role": "system", "content": "You are an expert career strategist and data analyst specializing in job market trends and application optimization."},
                    {"role": "user", "content": analysis_prompt}
                ],
                "temperature": 0.3,
                "max_tokens": 1500
            }
            
            response = requests.post(
                f"{self.base_url}/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                analysis_result = response.json()
                insights = analysis_result['choices'][0]['message']['content']
                
                # Store insights
                self.performance_data["learning_insights"]["last_ai_analysis"] = {
                    "timestamp": datetime.now().isoformat(),
                    "insights": insights,
                    "trigger_application": record["company"]
                }
                
                self.logger.info("AI insights generated successfully")
            
        except Exception as e:
            self.logger.error(f"Error generating AI insights: {e}")
    
    def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get current optimization recommendations"""
        recommendations = {
            "skill_recommendations": self._get_skill_recommendations(),
            "timing_recommendations": self._get_timing_recommendations(),
            "strategy_adjustments": self._get_strategy_adjustments(),
            "market_insights": self._get_market_insights(),
            "performance_summary": self._get_performance_summary()
        }
        
        return recommendations
    
    def _get_skill_recommendations(self) -> Dict[str, Any]:
        """Get skill-based recommendations"""
        skill_model = self.learning_models["skill_recommendation_model"]
        
        return {
            "top_performing_skills": skill_model.get("trending_skills", [])[:5],
            "skills_to_emphasize": [
                skill for skill, score in skill_model.get("skill_scores", {}).items()
                if score > 0.6
            ],
            "emerging_skills": self._identify_emerging_skills()
        }
    
    def _get_timing_recommendations(self) -> Dict[str, Any]:
        """Get timing-based recommendations"""
        timing_model = self.learning_models["timing_optimization_model"]
        
        best_times = timing_model.get("best_times", {})
        best_days = timing_model.get("best_days", {})
        
        # Find optimal times
        optimal_hours = sorted(best_times.items(), key=lambda x: x[1], reverse=True)[:3]
        optimal_days = sorted(best_days.items(), key=lambda x: x[1], reverse=True)[:3]
        
        return {
            "optimal_application_hours": [{"hour": int(h), "success_rate": r} for h, r in optimal_hours],
            "optimal_application_days": [{"day": d, "success_rate": r} for d, r in optimal_days],
            "avoid_times": self._get_times_to_avoid()
        }
    
    def _get_strategy_adjustments(self) -> Dict[str, Any]:
        """Get strategy adjustment recommendations"""
        model = self.learning_models["response_prediction_model"]
        weights = model.get("weights", {})
        
        adjustments = []
        
        # Analyze feature importance
        if weights.get("resume_customization_score", 0) > 0.3:
            adjustments.append({
                "type": "resume_customization",
                "recommendation": "Continue high level of resume customization - it's working well",
                "importance": "high"
            })
        
        if weights.get("timing_score", 0) > 0.2:
            adjustments.append({
                "type": "timing",
                "recommendation": "Application timing significantly impacts success",
                "importance": "medium"
            })
        
        return {
            "strategy_adjustments": adjustments,
            "model_confidence": model.get("accuracy", 0),
            "recommendation_strength": "high" if len(self.application_history) > 20 else "low"
        }
    
    def predict_application_success(self, application_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict likelihood of application success"""
        model = self.learning_models["response_prediction_model"]
        weights = model.get("weights", {})
        
        if not weights or len(self.application_history) < self.min_samples_for_learning:
            return {
                "success_probability": 0.5,
                "confidence": "low",
                "message": "Insufficient data for reliable prediction"
            }
        
        # Extract features
        features = self._extract_features(application_data)
        feature_names = model.get("features", [])
        
        # Calculate prediction
        score = 0.0
        for i, feature_name in enumerate(feature_names):
            if i < len(features):
                score += features[i] * weights.get(feature_name, 0)
        
        # Normalize to probability
        probability = max(0, min(1, (score + 1) / 2))
        
        confidence = "high" if model.get("accuracy", 0) > 0.7 else "medium"
        
        return {
            "success_probability": probability,
            "confidence": confidence,
            "model_accuracy": model.get("accuracy", 0),
            "feature_contributions": {
                feature_names[i]: features[i] * weights.get(feature_names[i], 0)
                for i in range(min(len(features), len(feature_names)))
            }
        }
    
    # Helper methods
    def _get_company_size(self, company: str) -> str:
        """Classify company size (placeholder - could use external API)"""
        # This could be enhanced with actual company data APIs
        large_companies = ["google", "microsoft", "amazon", "apple", "meta", "tesla"]
        if any(comp in company.lower() for comp in large_companies):
            return "large"
        return "unknown"
    
    def _get_company_size_score(self, company: str) -> float:
        """Get numerical score for company size"""
        size = self._get_company_size(company)
        return {"large": 0.8, "medium": 0.6, "small": 0.4, "startup": 0.3, "unknown": 0.5}.get(size, 0.5)
    
    def _get_industry(self, company: str) -> str:
        """Classify company industry (placeholder)"""
        tech_keywords = ["tech", "software", "ai", "data", "cloud"]
        if any(keyword in company.lower() for keyword in tech_keywords):
            return "technology"
        return "unknown"
    
    def _classify_role_type(self, position: str) -> str:
        """Classify role type"""
        position_lower = position.lower()
        if "senior" in position_lower or "lead" in position_lower:
            return "senior"
        elif "junior" in position_lower or "entry" in position_lower:
            return "junior"
        else:
            return "mid-level"
    
    def _calculate_skills_match_score(self, required_skills: List[str]) -> float:
        """Calculate how well our skills match requirements"""
        # This could be enhanced with actual user skill data
        user_skills = ["python", "javascript", "react", "sql", "aws"]  # From profile
        if not required_skills:
            return 0.5
        
        matches = len(set(skill.lower() for skill in required_skills) & set(user_skills))
        return matches / len(required_skills)
    
    def _get_timing_score(self, timestamp_str: str) -> float:
        """Calculate timing score based on when application was sent"""
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            hour = timestamp.hour
            day = timestamp.weekday()  # 0 = Monday
            
            # Business hours are better
            hour_score = 0.8 if 9 <= hour <= 17 else 0.4
            # Weekdays are better
            day_score = 0.8 if day < 5 else 0.3
            
            return (hour_score + day_score) / 2
        except:
            return 0.5
    
    def _calculate_model_accuracy(self, features: List[List[float]], labels: List[int], weights: Dict[str, float]) -> float:
        """Calculate model accuracy"""
        if not features or not labels:
            return 0.0
        
        correct = 0
        for i, feature_vector in enumerate(features):
            prediction = sum(feature_vector[j] * list(weights.values())[j] for j in range(len(feature_vector)))
            predicted_label = 1 if prediction > 0 else 0
            if predicted_label == labels[i]:
                correct += 1
        
        return correct / len(labels)
    
    def _identify_emerging_skills(self) -> List[str]:
        """Identify emerging skills based on recent trends"""
        if len(self.application_history) < 10:
            return []
        
        # Analyze skill frequency in recent vs older applications
        recent_apps = self.application_history[-20:]
        older_apps = self.application_history[-40:-20] if len(self.application_history) >= 40 else []
        
        recent_skills = Counter()
        older_skills = Counter()
        
        for app in recent_apps:
            for skill in app.get("skills_required", []):
                recent_skills[skill] += 1
        
        for app in older_apps:
            for skill in app.get("skills_required", []):
                older_skills[skill] += 1
        
        # Find skills that are trending up
        emerging = []
        for skill, recent_count in recent_skills.items():
            older_count = older_skills.get(skill, 0)
            if recent_count > older_count * 1.5:  # 50% increase
                emerging.append(skill)
        
        return emerging[:5]  # Top 5 emerging skills
    
    def _get_times_to_avoid(self) -> List[Dict[str, Any]]:
        """Get times/days to avoid applications"""
        timing_model = self.learning_models["timing_optimization_model"]
        best_times = timing_model.get("best_times", {})
        best_days = timing_model.get("best_days", {})
        
        avoid_times = []
        
        # Find hours with low success rates
        for hour, rate in best_times.items():
            if rate < 0.2:
                avoid_times.append({"type": "hour", "value": int(hour), "reason": "Low response rate"})
        
        # Find days with low success rates
        for day, rate in best_days.items():
            if rate < 0.3:
                avoid_times.append({"type": "day", "value": day, "reason": "Low response rate"})
        
        return avoid_times
    
    def _get_market_insights(self) -> Dict[str, Any]:
        """Get market insights from learning data"""
        insights = self.performance_data.get("learning_insights", {})
        return {
            "last_ai_analysis": insights.get("last_ai_analysis", {}),
            "skill_trends": self._identify_emerging_skills(),
            "market_changes": self._detect_market_changes()
        }
    
    def _detect_market_changes(self) -> List[Dict[str, Any]]:
        """Detect significant changes in market patterns"""
        changes = []
        
        # This could be enhanced with more sophisticated change detection
        if len(self.application_history) >= 30:
            recent_response_rate = sum(1 for app in self.application_history[-15:] if app["response_received"]) / 15
            older_response_rate = sum(1 for app in self.application_history[-30:-15] if app["response_received"]) / 15
            
            if abs(recent_response_rate - older_response_rate) > 0.2:
                changes.append({
                    "type": "response_rate_change",
                    "description": f"Response rate changed from {older_response_rate:.1%} to {recent_response_rate:.1%}",
                    "significance": "high" if abs(recent_response_rate - older_response_rate) > 0.3 else "medium"
                })
        
        return changes
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get overall performance summary"""
        if not self.application_history:
            return {"message": "No application history available"}
        
        total_apps = len(self.application_history)
        responses = sum(1 for app in self.application_history if app["response_received"])
        interviews = sum(1 for app in self.application_history if app["interview_scheduled"])
        offers = sum(1 for app in self.application_history if app["offer_received"])
        
        return {
            "total_applications": total_apps,
            "response_rate": responses / total_apps if total_apps > 0 else 0,
            "interview_rate": interviews / total_apps if total_apps > 0 else 0,
            "offer_rate": offers / total_apps if total_apps > 0 else 0,
            "trend": self._calculate_performance_trend(),
            "model_confidence": self.learning_models["response_prediction_model"].get("accuracy", 0)
        }
    
    def _calculate_performance_trend(self) -> str:
        """Calculate whether performance is improving or declining"""
        if len(self.application_history) < 10:
            return "insufficient_data"
        
        recent_rate = sum(1 for app in self.application_history[-10:] if app["response_received"]) / 10
        older_rate = sum(1 for app in self.application_history[-20:-10] if app["response_received"]) / 10
        
        if recent_rate > older_rate * 1.1:
            return "improving"
        elif recent_rate < older_rate * 0.9:
            return "declining"
        else:
            return "stable"
    
    def _save_learning_data(self):
        """Save all learning data to files"""
        try:
            # Save application history
            with open("data/application_history.json", 'w') as f:
                json.dump(self.application_history[-1000:], f, indent=2)  # Keep last 1000
            
            # Save performance data
            with open("data/performance_data.json", 'w') as f:
                json.dump(self.performance_data, f, indent=2)
            
            # Save learning models
            with open("data/learning_models.json", 'w') as f:
                json.dump(self.learning_models, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving learning data: {e}")