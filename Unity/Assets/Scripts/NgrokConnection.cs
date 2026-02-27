using System.Collections;
using System.Text;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

public class NgrokConnection : MonoBehaviour
{
    public TMP_InputField addressInput;
    public TMP_Text resultText;
    public TMP_Text speakText;
    public Button btn;

    public Color successColor;
    public Color robotDogColor;
    public Color thinkingColor;
    public Color errorColor;
    public SceneSwitch ss;
    public SpeechOutput speech;

    public bool IsRequestInFlight { get; private set; }

    public void TestConnection()
    {
        StartCoroutine(SendTestRequest());
    }

    public void SendQuestion(string question)
    {
        if (string.IsNullOrWhiteSpace(question))
        {
            return;
        }
        if (IsRequestInFlight)
        {
            return;
        }

        if (speakText != null)
        {
            speakText.text = "Thinking...";
            speakText.color = thinkingColor;
        }

        IsRequestInFlight = true;
        StartCoroutine(SendQuestionRequest(question));
    }

    public void SendEmergencyStop()
    {
        StartCoroutine(SendStopRequest());
    }

    private string BuildEndpoint(string route)
    {
        string subdomain = addressInput != null ? addressInput.text.Trim() : "";
        return "https://" + subdomain + ".ngrok-free.app/" + route;
    }

    private void ShowNetworkError()
    {
        const string message = "Couldn't connect - check your network and try again";
        if (resultText != null)
        {
            resultText.text = message;
            resultText.color = errorColor;
        }
        if (speakText != null)
        {
            speakText.text = "Can't reach Comet right now - check your connection.";
            speakText.color = errorColor;
        }
    }

    private IEnumerator SendQuestionRequest(string question)
    {
        string jsonPayload = JsonUtility.ToJson(new QuestionData(question));
        byte[] jsonToSend = Encoding.UTF8.GetBytes(jsonPayload);

        UnityWebRequest request = new UnityWebRequest(BuildEndpoint("ask_question"), "POST");
        request.uploadHandler = new UploadHandlerRaw(jsonToSend);
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();
        IsRequestInFlight = false;

        if (request.result == UnityWebRequest.Result.Success)
        {
            QuestionResponse res = JsonUtility.FromJson<QuestionResponse>(request.downloadHandler.text);
            if (res != null && !string.IsNullOrEmpty(res.response))
            {
                ProcessResponse(res.response);
            }
            else
            {
                if (speakText != null)
                {
                    speakText.text = "I heard you, but I need a second try.";
                    speakText.color = errorColor;
                }
            }
        }
        else
        {
            Debug.LogError("Question request failed: " + request.error);
            Debug.LogError("Response code: " + request.responseCode);
            Debug.LogError("Response text: " + request.downloadHandler.text);
            if (request.responseCode == 429 && speakText != null)
            {
                speakText.text = "I'm still thinking about your last request.";
                speakText.color = thinkingColor;
            }
            else
            {
                ShowNetworkError();
            }
        }
    }

    private IEnumerator SendStopRequest()
    {
        UnityWebRequest request = new UnityWebRequest(BuildEndpoint("stop_robot"), "POST");
        request.uploadHandler = new UploadHandlerRaw(Encoding.UTF8.GetBytes("{}"));
        request.downloadHandler = new DownloadHandlerBuffer();
        request.SetRequestHeader("Content-Type", "application/json");

        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            if (speakText != null)
            {
                speakText.text = "Stopping now.";
                speakText.color = robotDogColor;
            }
        }
        else
        {
            Debug.LogError("Stop request failed: " + request.error);
            ShowNetworkError();
        }
    }

    private IEnumerator SendTestRequest()
    {
        UnityWebRequest request = UnityWebRequest.Get(BuildEndpoint("test_connection"));
        yield return request.SendWebRequest();

        if (request.result == UnityWebRequest.Result.Success)
        {
            Debug.Log("Backend is reachable: " + request.downloadHandler.text);
            if (resultText != null)
            {
                resultText.text = "Connected to Comet";
                resultText.color = successColor;
                if (btn != null)
                {
                    ColorBlock colors = btn.colors;
                    colors.normalColor = successColor;
                    btn.colors = colors;
                }
                if (ss != null)
                {
                    ss.MenuPress();
                }
            }
        }
        else
        {
            Debug.LogError("Connection failed: " + request.error);
            ShowNetworkError();
        }
    }

    [System.Serializable]
    public class QuestionData
    {
        public string user_question;

        public QuestionData(string question)
        {
            user_question = question;
        }
    }

    [System.Serializable]
    public class QuestionResponse
    {
        public string response;
    }

    public void ProcessResponse(string response)
    {
        if (speech != null)
        {
            speech.Speak(response);
        }
        if (speakText != null)
        {
            speakText.text = response;
            speakText.color = robotDogColor;
        }
    }
}
