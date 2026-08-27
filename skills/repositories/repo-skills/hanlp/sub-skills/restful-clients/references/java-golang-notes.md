# Java and Golang RESTful Notes

Java Maven dependency:

```xml
<dependency><groupId>com.hankcs.hanlp.restful</groupId><artifactId>hanlp-restful</artifactId><version>0.0.15</version></dependency>
```

Java quick start:

```java
HanLPClient client = new HanLPClient("https://hanlp.hankcs.com/api", null);
System.out.println(client.parse("HanLP为生产环境带来次世代最先进的多语种NLP技术。"));
```

Go quick start:

```bash
go get -u github.com/hankcs/gohanlp@main
```

```go
client := hanlp.HanLPClient(hanlp.WithAuth(""))
result, err := client.Parse("In 2021, HanLPv2.1 delivers NLP.", hanlp.WithLanguage("mul"))
```

Endpoint URL, auth, quota, and supported language/task set are provider-specific. Route output interpretation to `../../document-and-data/SKILL.md`.
