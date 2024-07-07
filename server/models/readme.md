
#### `models`
Data models in the application layer, i.e. what the API endpoints see and may communicate to the client. 

###### Usage
All models are intended for client-server communication, except for `CoCoConfig`, which reads configuration variables from `.env`. 

```python
from .models import (
    GenerateRequest, VerifyRequest, SurveyRequest, 
    GenerateResponse, VerifyResponse, SurveyResponse,
    CoCoConfig  
)
```
