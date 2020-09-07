import React from "react";
import { Disqus, CommentCount } from "gatsby-plugin-disqus";

const DisqusComments = (props) => {
  let disqusConfig = {
    url: props.postURL,
    identifier: props.postURL,
    title: props.postTitle,
  };
  return (
    <>
      <h1>{props.postTitle}</h1>
      <CommentCount config={disqusConfig} placeholder={"..."} />
      {/* Post Contents */}
      <Disqus config={disqusConfig} />
    </>
  );
};

export default DisqusComments;
