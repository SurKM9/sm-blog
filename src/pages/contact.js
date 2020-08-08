import React from "react";
import Helmet from "react-helmet";
import { graphql } from "gatsby";
import Layout from "../components/layout";

const ContactPage = ({ data: { site } }) => {
  return (
    <Layout>
      <Helmet>
        <title>Contact — {site.siteMetadata.title}</title>
        <meta
          name="description"
          content={"Contact page of " + site.siteMetadata.description}
        />
      </Helmet>
      <div className="two-grids -contact">
        <div
          className="post-thumbnail"
          style={{
            backgroundImage: `url('/assets/alexander-andrews-HgUDpaGPTEA-unsplash.jpg')`,
            marginBottom: 0,
          }}
        >
          <h1 className="post-title">Get in Touch</h1>
          <p>Let me know what you think &rarr;</p>
        </div>
        <div>
          <form
            className="form-container"
            name="contact"
            method="post"
            data-netlify="true"
            onSubmit="submit"
          >
            {/* this is needed to connect netlify and gatsby */}
            <input type="hidden" name="form-name" value="contact" />
            <div>
              <label>
                Your Name: <input type="text" name="name" id="w3lName" />
              </label>
            </div>
            <div>
              <label>
                Your Email: <input type="email" name="email" id="w3lSender" />
              </label>
            </div>
            <div>
              <label>
                Subject: <input type="text" name="subject" id="w3lSubject" />
              </label>
            </div>
            <div>
              <label>
                Message: <textarea name="message" id="w3lMessage"></textarea>
              </label>
            </div>
            <div style={{ display: "flex", justifyContent: "flex-end" }}>
              <button
                type="submit"
                className="button -primary"
                style={{ marginRight: 0 }}
              >
                Submit this form
              </button>
            </div>
          </form>
        </div>
      </div>
    </Layout>
  );
};
export default ContactPage;
export const pageQuery = graphql`
  query ContactPageQuery {
    site {
      siteMetadata {
        title
        description
      }
    }
  }
`;
