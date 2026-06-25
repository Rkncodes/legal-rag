import { useEffect, useState } from "react";
import axios from "axios";
import "./App.css";

function App() {

  const [question, setQuestion] = useState("");
  const [answer, setAnswer] = useState("");
  const [keyword, setKeyword] = useState("");
  const [matches, setMatches] = useState([]);
  const [agreement, setAgreement] = useState("");
  const [agreements, setAgreements] = useState([]);
  const [loading, setLoading] = useState(false);
  const askQuestion = async () => {

    if (!question.trim()) return;

    try {

      setLoading(true);

      const response = await axios.post(
        "http://127.0.0.1:8000/ask",
        {
          question
        }
      );

      setAnswer(
        response.data.answer
      );

    } catch (err) {

      console.error(err);

      setAnswer(
        "Failed to connect to backend."
      );

    } finally {

      setLoading(false);

    }
  };

  const searchKeyword = async () => {
    if(!agreement) return;

  try {

    const response =
      await axios.get(
        "http://127.0.0.1:8000/keyword-search",
        {
          params: {
          keyword,
          agreement
}
        }
      );

    setMatches(
      response.data.matches
    );

  } catch (err) {

    console.error(err);

  }
};

useEffect(() => {

  axios
    .get(
      "http://127.0.0.1:8000/agreements"
    )
    .then((response) => {

      const pdfs =
        response.data?.agreements || [];

      console.log("PDFS:", pdfs);

      setAgreements(pdfs);

      if (pdfs.length > 0) {

        setAgreement(
          pdfs[0]
        );

      }

    })
    .catch((error) => {

      console.error(
        "Agreement load failed:",
        error
      );

    });

}, []);

  return (
    <div className="app">

      <aside className="sidebar">

        <div className="logo-card">

          <div className="logo-icon">
            ⚖️
          </div>

          <div>
            <h2>Legal RAG</h2>
            <p>Assistant</p>
          </div>

        </div>

        <div className="menu">

          <div className="menu-item active">
            Ask Question
          </div>

          <div className="menu-item">
            History
          </div>

          <div className="menu-item">
            About
          </div>

        </div>

        <div className="about-card">

          <h3>About</h3>

          <p>
            Ask questions across telecom agreements
            and retrieve grounded answers with citations.
          </p>

        </div>

      </aside>

      <main className="main">

        <div className="header">

          <h1>
            Legal RAG Assistant
          </h1>

          <p>
            Ask questions about your legal agreements
          </p>

        </div>

        <div className="card">

          <h2>Ask a Question</h2>

          <textarea
            value={question}
            onChange={(e) =>
              setQuestion(e.target.value)
            }
            placeholder="Type your legal question here..."
          />

          <button
            onClick={askQuestion}
          >
            {loading ? "Thinking..." : "Ask"}
          </button>

        </div>

        <div className="card">

          <h2>Answer</h2>

          <div className="answer-box">

            {
              answer
                ? <pre>{answer}</pre>
                : (
                  <div className="empty-state">
                    ⚖️
                    <p>Your answer will appear here</p>
                  </div>
                )
            }

          </div>

        </div>

        <div className="card">

  <h2>Keyword Search</h2>

  <p style={{
  marginBottom: "12px",
  color: "#93c5fd"
}}>
  Agreement
</p>
<div className="keyword-row">
<select
  value={agreement}
  onChange={(e) =>
    setAgreement(
      e.target.value
    )
  }
>

  {
    agreements.length === 0
      ? (
        <option value="">
          Loading agreements...
        </option>
      )
      : (
        agreements.map(
          (item) => (
            <option
              key={item}
              value={item}
            >
              {item
                .replace(".pdf", "")
                .replace(".PDF", "")
              }
            </option>
          )
        )
      )
  }

</select>

  <input
    type="text"
    value={keyword}
    onChange={(e) =>
      setKeyword(
        e.target.value
      )
    }
    placeholder="termination"
  />

  <button
    onClick={searchKeyword}
  >
    Search Keyword
  </button>

</div>
</div>

<div className="card">

  <h2>
  Keyword Results
  ({matches.length})
</h2>

  {
    matches?.map(
      (match, index) => (

        <div
          key={index}
          className="keyword-result"
        >

          <h4>
  Page {match.page_number}
</h4>

{
  match.heading &&
  (
    <p>
      {match.heading}
    </p>
  )
}


          <div
  dangerouslySetInnerHTML={{
    __html:
      match.snippet
        .replaceAll(
          "<<<HIGHLIGHT>>>",
          "<mark>"
        )
        .replaceAll(
          "<<<END>>>",
          "</mark>"
        )
  }}
/>

        </div>

      )
    )
  }

</div>

      </main>

    </div>
  );
}

export default App;