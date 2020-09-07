import React from "react";
import { Link } from "gatsby";

const PostLink = ({ post }) => (
  <article className="card ">
    <Link to={post.frontmatter.path}>
      {!!post.frontmatter.thumbnail && (
        <img
          src={post.frontmatter.thumbnail}
          alt={post.frontmatter.title + "- Featured Shot"}
        />
      )}
    </Link>
    <header>
      <h2 className="post-title">
        <Link to={post.frontmatter.path} className="post-link">
          {post.frontmatter.title}
        </Link>
      </h2>
      <div className="post-meta">{post.frontmatter.date}</div>
      <img
        src={"/assets/profile.jpeg"}
        alt={"profile-icon"}
        style={{
          height: 35,
          width: 35,
          borderRadius: 100,
          overflow: "hidden",
          position: "relative",
          left: 280,
          bottom: 25,
        }}
      />
    </header>
  </article>
);
export default PostLink;
